import sqlite3
import random
import string
from typing import Self
from functools import partial
import os
from dotenv import load_dotenv
import logging
from mistralai import Mistral
from mistralai.models import UserMessage, SystemMessage, AssistantMessage, ToolMessage
from functools import partial
import json
from getpass import getpass
import bcrypt
from datetime import datetime
import httpx

load_dotenv()

logging.basicConfig(level=logging.DEBUG,
                    filename='executed_commands.log',
                    format='\n %(message)s \n',
                    filemode='w')

def check_password(password):
    return bcrypt.checkpw(password.encode('utf-8'), b'$2b$12$eEkHgtcMIVJkbVXVTGWebucHHNGaT12lauuz6rxEwHcWBymqhOVa.')

class Mistral_Ai:
    def __init__(self, api: str, model: str,  system_prompt: str, desc_of_tools: dict[str, str | dict], tools: dict[str, partial]):
        self.api: str = api
        self.model: str = model
        self._client: Mistral = None
        self._librarian_ins: Librarian = Librarian()
        self._messages_sent: list[UserMessage | SystemMessage | AssistantMessage] = [SystemMessage(content=system_prompt)]
        self.desc_of_tools: dict[str, str | dict] = desc_of_tools
        self.tools: dict[str, partial] = tools

    def __enter__(self) -> Self:
        self._initilise_clients()
        return self
    
    def __exit__(self, exc_type, exc_value, traceback):
        self._client = None
        return None

    def _initilise_clients(self):
        if not self._client:
            self._client = Mistral(api_key=self.api)
        return None

    def text_gen(self, user_prompt: str) -> str | None:
 
        if user_prompt: self._messages_sent.append(UserMessage(content=user_prompt))
        else: print("Invalid Prompt"); return None
        
        while True:
            response = self._client.chat.complete(
                model = self.model,
                messages = self._messages_sent,
                tools = self.desc_of_tools if self.desc_of_tools else {},
                tool_choice = "auto",
                parallel_tool_calls = True
            )
            
            if not response: return None

            response = response.choices[0].message
            tool_calls = response.tool_calls
            if tool_calls:
                for tool_call in response.tool_calls:
                    logging.warning(f"Recieved a function call!")
                    self._messages_sent.append(AssistantMessage(tool_calls=[tool_call]))
                    func_name = tool_call.function.name
                    func_params = json.loads(tool_call.function.arguments)
                    callable_func = getattr(Librarian, func_name)
                    func_results = callable_func(self._librarian_ins, **func_params)
                    logging.warning(f"Executed: {func_name}({func_results})\n\nReturned:{func_results}\n-----------------------------")
                    self._messages_sent.append(ToolMessage(name=func_name, content=str(func_results), tool_call_id=tool_call.id))
                continue

            text_response = response.content
            self._messages_sent.append(AssistantMessage(content=text_response))
            return text_response

class Librarian:

    def __init__(self):
        conn = sqlite3.connect("library.db")
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.row_factory = sqlite3.Row
        self.conn = conn
        self.cur = self.conn.cursor()
        self._create_tables()
        logging.warning("INITILISED LIBRARIAN")

    @staticmethod
    def _generate_unique_id(prefix: str = "book") -> str:
        chars = string.ascii_lowercase + string.digits
        random_part = ''.join(random.choice(chars) for _ in range(8))
        return f"{prefix}_{random_part}"

    @staticmethod
    def _format_rows_to_string(rows: list[sqlite3.Row]) -> str:
        if not rows:
            return "Query returned no results."
        list_of_dicts = [dict(row) for row in rows]
        return str(list_of_dicts)

    def add_book(self, title: str, author: str, isbn: str, quantity: int) -> None:
        if not all([title, author, isbn, quantity]):
            return ("\nERROR: All fields (title, author, isbn, quantity) are required.\n")
        try:
            book_id = self._generate_unique_id()
            self.cur.execute('''
                INSERT INTO books (book_id, title, author, isbn, quantity, amount_of_times_rented)
                VALUES (?, ?, ?, ?, ?, 0)
            ''', (book_id, title, author, isbn, int(quantity)))
            self.conn.commit()
            return (f"\nSuccessfully added '{title}' by {author} to the library.\n")
        except sqlite3.IntegrityError:
            return (f"\nERROR: A book with ISBN '{isbn}' already exists.\n")
        except Exception as e:
            return (f"\nAn unexpected error occurred: {e}\n")
        finally:
            self.conn.close()

    def _create_tables(self) -> None:

        self.cur.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                full_name TEXT NOT NULL,
                gender TEXT NOT NULL,
                age INTEGER NOT NULL
            );''')

        self.cur.execute(
            '''CREATE TABLE IF NOT EXISTS books (
                book_id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                author TEXT NOT NULL,
                isbn TEXT NOT NULL UNIQUE,
                quantity INTEGER NOT NULL,
                amount_of_times_rented INTEGER NOT NULL
            );''')
        
        self.cur.execute(        
            '''CREATE TABLE IF NOT EXISTS rentals (
                rental_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                book_id TEXT NOT NULL,
                rental_date TEXT NOT NULL,
                return_date TEXT,
                FOREIGN KEY (user_id) REFERENCES users (user_id),
                FOREIGN KEY (book_id) REFERENCES books (book_id)
            );''')
    
    def __enter__(self) -> Self:
        self._initialise_from_csv("books.csv")
        return self
    
    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.conn.commit()
        self.conn.close()
        return None
    
    @staticmethod
    def _format_sql_for_display(sql_template, params):
        if not params:
            return sql_template

        formatted_params = []
        for p in params:
            if isinstance(p, str):

                formatted_params.append(f"'{p.replace("'", "''")}'")
            elif isinstance(p, (int, float)):
                formatted_params.append(str(p))
            elif p is None:
                formatted_params.append("NULL")
            elif isinstance(p, bytes):
                formatted_params.append(f"X'{p.hex()}'")
            else:
                formatted_params.append(str(p))

        parts = sql_template.split('?')
        if len(parts) - 1 != len(formatted_params):
            return f"ERROR: Mismatch in parameters for SQL: {sql_template} with params: {params}"

        display_query = parts[0]
        for i in range(len(formatted_params)):
            display_query += formatted_params[i] + parts[i+1]

        return display_query

    def add_user(self, full_name: str, gender: str, age: int) -> str:
        if not all([full_name, gender, age]):
            return "\nERROR: All fields (full_name, gender, age) are required.\n"
        try:
            user_id = self._generate_unique_id(prefix="user")
            self.cur.execute(
                "INSERT INTO users (user_id, full_name, gender, age) VALUES (?, ?, ?, ?)",
                (user_id, full_name, gender, age)
            )
            self.conn.commit()
            return f"\nSuccessfully added user '{full_name}' with ID '{user_id}'.\n"
        except sqlite3.Error as e:
            return f"\nAn unexpected error occurred: {e}\n"

    def delete_user(self, user_id: str) -> str:
        self.cur.execute('SELECT full_name FROM users WHERE user_id = ?', (user_id,))
        row = self.cur.fetchone()

        if not row:
            return f"\nERROR: User with ID '{user_id}' not found.\n"

        user_name = row['full_name']
        confirm = input(f"Are you sure you want to delete user '{user_name}' (ID: {user_id})? This will fail if they have active rentals. (yes/no): ").lower().strip()

        if confirm == 'yes':
            try:
                self.cur.execute('DELETE FROM users WHERE user_id = ?', (user_id,))
                self.conn.commit()
                if self.cur.rowcount > 0:
                    return f"\nSuccessfully deleted user '{user_name}'.\n"
                else:
                    return f"\nERROR: Could not delete user with ID '{user_id}'.\n"
            except sqlite3.IntegrityError:
                return f"\nERROR: Cannot delete user '{user_name}'. They are likely linked to active rental records.\n"
            except sqlite3.Error as e:
                return f"\nAn error occurred during deletion: {e}\n"
        else:
            return "\nDeletion cancelled.\n"

    def delete_book(self, book_id: str) -> None:

        self.cur.execute('SELECT title FROM books WHERE book_id = ?', (book_id,))
        row = self.cur.fetchone()

        if not row:
            self.conn.close()
            return (f"\nERROR: Book with ID '{book_id}' not found.\n")

        book_title = row['title']
        
        confirm = input(f"Are you sure you want to delete '{book_title}' (ID: {book_id})? This action cannot be undone. (yes/no): ").lower().strip()

        if confirm == 'yes':
            try:
                self.cur.execute('DELETE FROM books WHERE book_id = ?', (book_id,))
                self.conn.commit()
                if self.cur.rowcount > 0:
                    self.conn.close()
                    return(f"\nSuccessfully deleted '{book_title}'.\n")
                else:
                    self.conn.close()
                    return(f"\nERROR: Could not delete book with ID '{book_id}'.\n")
            except sqlite3.Error as e:
                self.conn.close()
                return(f"\nAn error occurred during deletion: {e}\n")
        else:
            self.conn.close()
            return("\nDeletion cancelled.\n")

    def get_current_date(self) -> str:
        return datetime.now().strftime("%d/%m/%Y")

    def add_rental(self, user_id: str, book_id: str, rental_date: str) -> str:
        try:
            self.cur.execute("SELECT 1 FROM users WHERE user_id = ?", (user_id,))
            if not self.cur.fetchone():
                return f"Error: User with ID '{user_id}' does not exist."

            self.cur.execute("SELECT quantity FROM books WHERE book_id = ?", (book_id,))
            book_row = self.cur.fetchone()
            if not book_row:
                return f"Error: Book with ID '{book_id}' does not exist."

            if book_row['quantity'] < 1:
                return f"Error: Book with ID '{book_id}' is out of stock."

            rental_id = self._generate_unique_id(prefix="rent")

            self.cur.execute(
                "INSERT INTO rentals (rental_id, user_id, book_id, rental_date) VALUES (?, ?, ?, ?)",
                (rental_id, user_id, book_id, rental_date)
            )

            self.cur.execute(
                "UPDATE books SET quantity = quantity - 1, amount_of_times_rented = amount_of_times_rented + 1 WHERE book_id = ?",
                (book_id,)
            )

            self.conn.commit()
            return f"Successfully created rental record '{rental_id}' for user '{user_id}' and book '{book_id}'."

        except sqlite3.Error as e:
            self.conn.rollback() 
            return f"Database error during rental: {e}"

    def return_book(self, rental_id: str, return_date: str) -> str:
        try:
            self.cur.execute("SELECT book_id, return_date FROM rentals WHERE rental_id = ?", (rental_id,))
            rental_row = self.cur.fetchone()

            if not rental_row:
                return f"Error: Rental with ID '{rental_id}' not found."
            if rental_row['return_date'] is not None:
                return f"Error: This book was already returned on {rental_row['return_date']}."

            book_id_to_return = rental_row['book_id']

            self.cur.execute(
                "UPDATE rentals SET return_date = ? WHERE rental_id = ?",
                (return_date, rental_id)
            )

            self.cur.execute(
                "UPDATE books SET quantity = quantity + 1 WHERE book_id = ?",
                (book_id_to_return,)
            )

            self.conn.commit()
            return f"Successfully processed return for rental ID '{rental_id}'."

        except sqlite3.Error as e:
            self.conn.rollback()
            return f"Database error during return: {e}"

    def execute_sql(self, prompt: str, params: tuple = ()) -> str:

        passkey_input = getpass(f"You are about to execute '{Librarian._format_sql_for_display(prompt, params)}' This is an irreverasable change!\nEnter your password to confirm: ")
        if not check_password(passkey_input): print("INVALID PASSWORD! ABORTING"); return "User entered te wrong password to authorise this action"

        try:
            self.cur.execute(prompt, tuple(params))
            if self.cur.description:
                return self._format_rows_to_string(self.cur.fetchall())
            return "SQL executed successfully, no rows returned."
        except sqlite3.Error as e:
            return f"Error executing SQL: {e}"

    def mass_execute(self, operations: list[tuple[str, tuple]]) -> str:
        results = []
        passkey_input = getpass(f"You are about to execute '{"\n\n".join([Librarian._format_sql_for_display(prompt, params) for prompt, params in operations])}' This is an irreverasable change!\nEnter your password to confirm: ")
        if not check_password(passkey_input): print("INVALID PASSWORD! ABORTING"); return "User entered the wrong password to authorise this action"
        for prompt, params in operations:
            try:
                self.cur.execute(prompt, tuple(params))
                if self.cur.description:
                    results.append(str(self.cur.fetchall()))
                else:
                    results.append("SQL executed successfully, no rows returned.")
            except sqlite3.Error as e:
                results.append(f"Error executing SQL: {e}")
        return self._format_rows_to_string(results)

    def fetch_data(self, prompt: str, params: tuple = ()) -> str:
        try:
            self.cur.execute(prompt, tuple(params))
            return self._format_rows_to_string(self.cur.fetchall())
        except sqlite3.Error as e:
            return f"Error fetching data: {e}"

    
if __name__ == "__main__":

    tools_json = [
    {
        "type": "function",
        "function": {
            "name": "get_current_date",
            "description": "A utility function that returns the current date as a string in DD/MM/YYYY format. Use this to get the date for new rentals or returns.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "add_rental",
            "description": "The primary function for renting a book. It creates a rental record, links a user to a book, and updates the book stock. Requires a user ID, a book ID, and the rental date.",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "string",
                        "description": "The unique ID of the user renting the book."
                    },
                    "book_id": {
                        "type": "string",
                        "description": "The unique ID of the book being rented."
                    },
                    "rental_date": {
                        "type": "string",
                        "description": "The date of the rental in DD/MM/YYYY format, obtained from get_current_date."
                    }
                },
                "required": ["user_id", "book_id", "rental_date"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "return_book",
            "description": "The primary function for returning a book. It marks a rental as complete and updates the book stock. Requires the unique ID of the rental record and the return date.",
            "parameters": {
                "type": "object",
                "properties": {
                    "rental_id": {
                        "type": "string",
                        "description": "The unique ID of the rental record being completed."
                    },
                    "return_date": {
                        "type": "string",
                        "description": "The date of the return in DD/MM/YYYY format, obtained from get_current_date."
                    }
                },
                "required": ["rental_id", "return_date"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "add_user",
            "description": "Adds a new user (renter) to the database with a specific full name, gender, and age.",
            "parameters": {
                "type": "object",
                "properties": {
                    "full_name": { "type": "string", "description": "The user's full name." },
                    "gender": { "type": "string", "description": "The user's gender." },
                    "age": { "type": "integer", "description": "The user's age." }
                },
                "required": ["full_name", "gender", "age"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "delete_user",
            "description": "Deletes a user from the database by their unique user ID. Requires user confirmation.",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_id": { "type": "string", "description": "The unique identifier of the user to be deleted." }
                },
                "required": ["user_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "add_book",
            "description": "Adds a single new book to the library with a specific title, author, ISBN, and quantity.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": { "type": "string", "description": "The full title of the book." },
                    "author": { "type": "string", "description": "The name of the book's author." },
                    "isbn": { "type": "string", "description": "The unique 13-digit ISBN of the book." },
                    "quantity": { "type": "integer", "description": "The number of copies of this book to add to the stock." }
                },
                "required": ["title", "author", "isbn", "quantity"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "delete_book",
            "description": "Deletes a book from the library database using its unique book ID. Requires user confirmation.",
            "parameters": {
                "type": "object",
                "properties": {
                    "book_id": { "type": "string", "description": "The unique identifier of the book to be deleted." }
                },
                "required": ["book_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "execute_sql",
            "description": "Executes a single, high-privilege SQL query that modifies the database. Requires a password. The query MUST use '?' placeholders for values to prevent injection.",
            "parameters": {
                "type": "object",
                "properties": {
                    "prompt": {
                        "type": "string",
                        "description": "The SQL query string, using '?' for placeholders."
                    },
                    "params": {
                        "type": "array",
                        "description": "A list of parameters to substitute into placeholders. Provide an empty list [] if the prompt contains no placeholders.",
                        "items": {}
                    }
                },
                "required": ["prompt", "params"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "mass_execute",
            "description": "Executes a list of SQL queries with their corresponding parameters in a single batch operation.",
            "parameters": {
                "type": "object",
                "properties": {
                    "operations": {
                        "type": "array",
                        "description": "A list of operations. Each operation is a two-item list containing the [SQL_query_string, parameters_list].",
                        "items": {
                            "type": "array",
                            "items": [
                                { "type": "string", "description": "The SQL sattement which may (should) or may not contain ? as palceholders"},
                                { "type": "array", "items": {} }
                            ]
                        }
                    }
                },
                "required": ["operations"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "fetch_data",
            "description": "Executes a read-only SQL SELECT query to fetch data. The query MUST use '?' placeholders for values in the WHERE clause to prevent injection.",
            "parameters": {
                "type": "object",
                "properties": {
                    "prompt": {
                        "type": "string",
                        "description": "The SQL SELECT query string, using '?' for placeholders."
                    },
                    "params": {
                        "type": "array",
                        "description": "A list of parameters to substitute into placeholders. Provide an empty list [] if the prompt contains no placeholders.",
                        "items": {}
                    }
                },
                "required": ["prompt", "params"]
            }
        }
    }
]
    list_of_tools = [
        "get_current_date",
        "add_rental",
        "return_book",
        "add_user",
        "delete_user",
        "add_book",
        "delete_book",
        "execute_sql",
        "mass_execute",
        "fetch_data"
    ]
    system_prompt = '''You are 'Librarian-AI,' a specialized and helpful assistant for the head librarian. Your primary directive is to provide the librarian with requested information accurately and to execute database modifications safely.

Your capabilities are defined by the following tools, which you must use in this order of preference:


1. PREFERRED HIGH-LEVEL TOOLS (Use these first for ALL common tasks):

   - add_rental / return_book: Your primary tools for managing rentals. Use these instead of raw SQL.
   - add_book / delete_book: Your primary tools for managing the book catalog.
   - add_user / delete_user: Your primary tools for managing user records.
   - get_current_date: A utility to fetch today's date, which you MUST use for all new rentals and returns.
   - fetch_data: Your primary tool for answering ANY question about the library's data (e.g., "list all books", "who has book X?").


2. POWERFUL SQL EXECUTION TOOLS (Use ONLY as a last resort):

   - execute_sql / mass_execute: Use these only for rare, complex operations that cannot be handled by the high-level tools above. These require a password and should be used sparingly.


RENTAL AND RETURN WORKFLOW (CRITICAL):

   To process a new rental:
   1. Acknowledge the request. Ask for the user_id and book_id if they are not provided.
   2. Call `get_current_date` to get today's date.
   2.5. ASk the user for a name or book_title
   use the book title to find it's id from the books table and the user_id from the users table
   if the user doesn't exist, ask the librarian to provide the rentee's full name, age, and gender
   3. Call `add_rental` using the user_id, book_id, and the date you just fetched.
   4. Report the outcome (success or error message) to the librarian.

   To process a book return:
   1. Acknowledge the request. Ask for the rental_id. If the librarian doesn't have it, help them find it by asking for the user and book details and using `fetch_data`.
   2. Call `get_current_date` to get today's date.
   3. Call `return_book` using the rental_id and the date.
   4. Report the outcome to the librarian.

   If the librarian asks about a rental
    1. Look up the rental on the rent table
    2. fetch the infor of the user and the book from teh user and book tbale
    3. provide this information to teh libarian

ANSWERING RENTAL AND USER QUESTIONS (CRITICAL):

When the librarian asks who has a specific book, or which books a specific user has rented, you MUST use the `fetch_data` tool to construct a SQL query that JOINS the necessary tables. Do not try to answer from memory.
   - To find who has a book: JOIN users, rentals, and books.
   - To find which books a user has: JOIN users, rentals, and books.
   - etc


KEY OPERATING RULES:

   - Confirm Before Modifying: Before using a modification tool, state what you are about to do and ask for confirmation.
   - Gather Information: If you lack necessary details for an operation, you MUST ask for them.
   - NEVER Alter the Schema: You are strictly forbidden from using ALTER TABLE or CREATE TABLE.


DATABASE SCHEMA REFERENCE:
   - books: (book_id, title, author, isbn, quantity, amount_of_times_rented)
   - users: (user_id, full_name, gender, age)
   - rentals: (rental_id, user_id, book_id, rental_date, return_date)

ANSWERING SUGGESTIONS
    - If the librarian asks a question, sucha s a suggestion, you MUST fetch all the title of all books in stock( You are to NEVER suggest books which are not in the databse), and use your own knowledge abaout said books to provide recomendations and suggestions
    - You will NEVER EVER mention ANY book that isn't in our database EVER!


CRITICAL FORMATTING RULE:
All of your responses MUST be plain text. Do NOT use any markdown formatting such as astrisks, underscores, etc. Use newlines, double newlines, and indentation to structure your output for maximum clarity in a command-line interface. If the user wishes to exit, they need ot press Ctrl+C'''

    with Mistral_Ai(os.getenv("MISTRAL_KEY"), "mistral-large-latest", system_prompt, tools_json, list_of_tools) as mist_cli:
        os.system("clear")
        while True:
            try:
                command = input("<<YOU>>: ")
                print(f"\n<<Library Assistant>>:\n--------------------\n{mist_cli.text_gen(command)}\n")
                continue
            except httpx.ConnectError:
                print(f"\n<<Library Assistant>>:\n--------------------\nYour internet connection is not stable. Please try again in a few minutes\n")
                continue
            except KeyboardInterrupt:
                print("\n<<Library Assistant>>:\n--------------------\nExiting...\n")
                break