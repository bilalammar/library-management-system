import sqlite3
import random
import string
import re
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
    def format_sql_for_display(sql_template, params):
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

    def execute_sql(self, prompt: str, params: tuple = ()) -> str:

        passkey_input = getpass(f"You are about to execute '{Librarian.format_sql_for_display(prompt, params)}' This is an irreverasable change!\nEnter your password to confirm: ")
        if not check_password(passkey_input): print("INVALID PASSWORD! ABORTING"); return "User entered te wrong password to authorise this action"

        try:
            self.cur.execute(prompt, params)
            if self.cur.description:
                return self._format_rows_to_string(self.cur.fetchall())
            return "SQL executed successfully, no rows returned."
        except sqlite3.Error as e:
            return f"Error executing SQL: {e}"

    def mass_execute(self, operations: list[tuple[str, tuple]]) -> str:
        results = []
        passkey_input = getpass(f"You are about to execute '{"\n\n".join([Librarian.format_sql_for_display(prompt, params) for prompt, params in operations])}' This is an irreverasable change!\nEnter your password to confirm: ")
        if not check_password(passkey_input): print("INVALID PASSWORD! ABORTING"); return "User entered te wrong password to authorise this action"
        for prompt, params in operations:
            try:
                self.cur.execute(prompt, params)
                if self.cur.description:
                    results.append(str(self.cur.fetchall()))
                else:
                    results.append("SQL executed successfully, no rows returned.")
            except sqlite3.Error as e:
                results.append(f"Error executing SQL: {e}")
        return self._format_rows_to_string(results)

    def fetch_data(self, prompt: str, params: tuple = ()) -> str:
        try:
            self.cur.execute(prompt, params)
            return self._format_rows_to_string(self.cur.fetchall())
        except sqlite3.Error as e:
            return f"Error fetching data: {e}"

    
if __name__ == "__main__":

    tools_json = [
    {
        "type": "function",
        "function": {
            "name": "add_book",
            "description": "Adds a single new book to the library with a specific title, author, ISBN, and quantity.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "The full title of the book."
                    },
                    "author": {
                        "type": "string",
                        "description": "The name of the book's author."
                    },
                    "isbn": {
                        "type": "string",
                        "description": "The unique 13-digit ISBN of the book."
                    },
                    "quantity": {
                        "type": "integer",
                        "description": "The number of copies of this book to add to the stock."
                    }
                },
                "required": ["title", "author", "isbn", "quantity"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "delete_book",
            "description": "Deletes a book from the library database using its unique book ID. This action is permanent and requires user confirmation via an input prompt.",
            "parameters": {
                "type": "object",
                "properties": {
                    "book_id": {
                        "type": "string",
                        "description": "The unique identifier of the book to be deleted (e.g., 'book_a1b2c3d4')."
                    }
                },
                "required": ["book_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "execute_sql",
            "description": "Executes a single, high-privilege SQL query that modifies the database (e.g., INSERT, UPDATE, DELETE). This action is irreversible and requires a password. The query MUST use '?' placeholders for all values.",
            "parameters": {
                "type": "object",
                "properties": {
                    "prompt": {
                        "type": "string",
                        "description": "The SQL query string with '?' placeholders."
                    },
                    "params": {
                        "type": "array",
                        "description": "A list of parameters to safely substitute into the SQL query's placeholders. Provide an empty list [] if the query has no parameters.",
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
            "description": "Executes a list of SQL queries with their corresponding parameters in a single batch operation. Useful for performing multiple modifications at once.",
            "parameters": {
                "type": "object",
                "properties": {
                    "operations": {
                        "type": "array",
                        "description": "A list of operations. Each operation is a two-item list containing the [SQL_query_string, parameters_list].",
                        "items": {
                            "type": "array",
                            "items": [
                                {
                                    "type": "string"
                                },
                                {
                                    "type": "array",
                                    "items": {}
                                }
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
            "description": "Executes a read-only SQL SELECT query to fetch data from the database. The query MUST use '?' placeholders for all values in the WHERE clause.",
            "parameters": {
                "type": "object",
                "properties": {
                    "prompt": {
                        "type": "string",
                        "description": "The SQL SELECT query string with '?' placeholders."
                    },
                    "params": {
                        "type": "array",
                        "description": "A list of parameters to safely substitute into the SQL query's placeholders. Provide an empty list [] if the query has no parameters.",
                        "items": {}
                    }
                },
                "required": ["prompt", "params"]
            }
        }
    }
]
    list_of_tools = [
    "add_book",
    "delete_book",
    "execute_sql",
    "mass_execute",
    "fetch_data"
    ]
    system_prompt = '''You are 'Librarian-AI,' a specialized and helpful assistant for the head librarian. Your primary directive is to provide the librarian with requested information accurately and to execute database modifications safely. You are expected to be helpful and forthcoming; when the librarian asks for data, your job is to fetch it using the appropriate tools without questioning their intent.

Your capabilities are defined by the following tools, which you must use in this order of preference:


1. PREFERRED HIGH-LEVEL TOOLS (Use these first whenever possible):

   - fetch_data: This is your primary tool for answering ANY question about the library's data. If the user asks "who," "what," "which books," "list users," etc., use this tool.

   - add_book: Use this specific function when the librarian wants to add a new book. It is safer and simpler than writing a raw SQL INSERT statement.

   - delete_book: Use this specific function to delete a book by its ID.


2. POWERFUL SQL EXECUTION TOOLS (Use ONLY when the task cannot be done by the tools above):

   - execute_sql: Use this for single database modifications like UPDATE (e.g., marking a book as returned) or INSERT into the 'users' or 'rentals' tables. Be aware that this is a high-privilege tool that will require the librarian to enter a password.

   - mass_execute: Use this for batch operations, such as adding multiple new users or recording several rentals at once. This is also a high-privilege tool that requires a password.


KEY OPERATING RULES:

   - Confirm Before Modifying: Before using add_book, delete_book, execute_sql, or mass_execute, you MUST state exactly what you are about to do and ask the librarian for confirmation.

   - Gather Information: If you lack the necessary details for an operation (like a user's age or a book's ISBN), you MUST ask the librarian for the missing information.

   - NEVER Alter the Schema: You are strictly forbidden from using ALTER TABLE or CREATE TABLE. Your role is to manage data within the existing structure, not to change the structure itself.

   - Suggest from Stock Only: When asked for a book recommendation, you must first use fetch_data to get a list of available books, and then provide suggestions ONLY from that list.


DATABASE SCHEMA REFERENCE:

   - books: (book_id, title, author, isbn, quantity, amount_of_times_rented)

   - users: (user_id, full_name, gender, age)

   - rentals: (rental_id, user_id, book_id, rental_date, return_date)


CRITICAL FORMATTING RULE:

All of your responses MUST be plain text. Do NOT use any markdown formatting like asterisks for lists or bolding. Use newlines, double newlines, and indentation to structure your output for maximum clarity in a command-line interface.'''

    with Mistral_Ai(os.getenv("MISTRAL_KEY"), "mistral-large-latest", system_prompt, tools_json, list_of_tools) as mist_cli:
        os.system("clear")
        while True:
            try:
                command = input("<<YOU>> ")
                print()
                print(f"<<BOT>> {mist_cli.text_gen(command)}\n")
                continue
            except KeyboardInterrupt:
                print("\nExiting...")
                break