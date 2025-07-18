import sqlite3
import csv
from pathlib import Path
import os
import sys

class Books:

    def __init__(self, book_id: str, title: str, author: str, isbn: str, quantity: int, amount_of_times_rented: int) -> None:
        self.book_id = str(book_id)
        self.title = str(title)
        self.author = str(author)
        self.isbn = str(isbn)
        self.quantity = int(quantity) if isinstance(quantity, (int, float)) or (isinstance(quantity, str) and quantity.isdigit()) else 0
        self.amount_of_times_rented = int(amount_of_times_rented) if isinstance(amount_of_times_rented, (int, float)) or (isinstance(amount_of_times_rented, str) and amount_of_times_rented.isdigit()) else 0

    @staticmethod
    def _get_db_connection():
        conn = sqlite3.connect("library.db")
        conn.row_factory = sqlite3.Row 
        return conn

    @staticmethod
    def create_table() -> None:
        conn = Books._get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS books (
                book_id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                author TEXT NOT NULL,
                isbn TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                amount_of_times_rented INTEGER NOT NULL
            )
        ''')
        conn.commit()
        conn.close()

    @staticmethod
    def get_book(book_id: str):
        conn = Books._get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM books WHERE book_id = ?', (book_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return Books(row['book_id'], row['title'], row['author'], row['isbn'], row['quantity'], row['amount_of_times_rented'])
        return None

    @staticmethod
    def view(display_amount: int = 5) -> None:
        display_amount = int(display_amount) if isinstance(display_amount, (int, float)) or (isinstance(display_amount, str) and display_amount.isdigit()) else 0
        if not display_amount:
            print("ERROR: Display amount should be a number!")
            return None

        conn = Books._get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM books LIMIT ?', (display_amount,))
        rows = cursor.fetchall()
        conn.close()

        print("------------Books------------")
        if not rows:
            print("No books found in the database.")
            return

        for item in rows:
            print("-----------------------------")
            print(f"Book Id:  {item['book_id']}")
            print(f"Title:    {item['title']}")
            print(f"Author:   {item['author']}")
            print(f"ISBN:     {item['isbn']}")
            print(f"Stock     {item['quantity']}")
            print(f"AOTR      {item['amount_of_times_rented']}")
            print("-----------------------------")
        return None

    @staticmethod
    def initialise_from_csv(path: str) -> None:
        Books.create_table()
        if not Path(path).exists(): print("No 'books.csv' file found. Skipping initilisation"); return None
        with open(path, "r") as f:
            reader = csv.DictReader(f)
            conn = Books._get_db_connection()
            cursor = conn.cursor()
            for item in list(reader):
                book_id = item.get('book_id', 'NA')
                title = item.get('title', 'NA').capitalize()
                author = item.get('author', 'NA')
                isbn = item.get('isbn', 'NA')
                quantity = item.get('quantity', '0')
                amount_of_times_rented = item.get('amount_of_times_rented', '0')
                
                quantity = int(quantity) if isinstance(quantity, (int, float)) or (isinstance(quantity, str) and quantity.isdigit()) else 0
                amount_of_times_rented = int(amount_of_times_rented) if isinstance(amount_of_times_rented, (int, float)) or (isinstance(amount_of_times_rented, str) and amount_of_times_rented.isdigit()) else 0

                cursor.execute('''
                    INSERT OR REPLACE INTO books (book_id, title, author, isbn, quantity, amount_of_times_rented)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (book_id, title, author, isbn, quantity, amount_of_times_rented))
            conn.commit()
            conn.close()
        return None

    @staticmethod
    def update_quantity(book_id: str, new_quantity: int, disp_log: bool = True) -> None:
        if new_quantity <= 0:
            print("\nERROR: New quantity may not be less than or equal to zero.\n")
            return None

        conn = Books._get_db_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE books SET quantity = ? WHERE book_id = ?', (new_quantity, book_id))
        conn.commit()

        if cursor.rowcount > 0:
            cursor.execute('SELECT title FROM books WHERE book_id = ?', (book_id,))
            book_title = cursor.fetchone()['title']
            if disp_log: print(f"\nSuccessfully updated the quantity of '{book_title}' to {new_quantity}.\n")
        else:
            print(f"\nERROR: Book Id '{book_id}' not found in database.\n")
        conn.close()
        return None

    @staticmethod
    def add_to_rentee_ammount(book_id: str, disp_log: bool = True) -> None:
        conn = Books._get_db_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE books SET amount_of_times_rented = amount_of_times_rented + 1 WHERE book_id = ?', (book_id,))
        conn.commit()

        if cursor.rowcount > 0:
            cursor.execute('SELECT title FROM books WHERE book_id = ?', (book_id,))
            book_title = cursor.fetchone()['title']
            if disp_log: print(f"\nSuccessfully incremented the AOTR of '{book_title}' by one.\n")
        else:
            print(f"\nERROR: Book Id '{book_id}' not found in database.\n")
        conn.close()
        return None 
    
    @staticmethod
    def get_book_rank_by_stat_n_amount(stat: str, disp_amount: int) -> None:
        '''
        # PARMS

        **Stat:** The state by which you want to rank by (title, author, amount_of_times_rented_asc, amount_of_times_rented_desc)

        **Disp_amount:** Amount of results to display
        '''

        ALLOWED_SORT_COLUMNS = {
        "title": "title",
        "author": "author",
        "amount_of_times_rented_asc": "amount_of_times_rented ASC",
        "amount_of_times_rented_desc": "amount_of_times_rented DESC"}

        order_by_clause = ALLOWED_SORT_COLUMNS.get(stat, None)

        if order_by_clause is None:
            # Handle invalid input (e.g., raise an error, use a default sort)
            print(f"Warning: Invalid sort parameter '{stat}'")
            return None


        conn = Books._get_db_connection()
        cursor = conn.cursor()
        cursor.execute(f'SELECT * FROM books ORDER BY {order_by_clause} LIMIT ?', (disp_amount,))
        rows = cursor.fetchall()
        conn.close()

        print("------------Books------------")
        if not rows:
            print("No books found in the database.")
            return

        for item in rows:
            print("-----------------------------")
            print(f"Book Id:  {item['book_id']}")
            print(f"Title:    {item['title']}")
            print(f"Author:   {item['author']}")
            print(f"ISBN:     {item['isbn']}")
            print(f"Stock     {item['quantity']}")
            print(f"AOTR      {item['amount_of_times_rented']}")
            print("-----------------------------")
        return None
        

class Person:

    def __init__(self, name: str, age: int, money: float = 0.00) -> None:
        self.name: str = str(name).capitalize()
        self.age: int = int(age) if isinstance(age, (int, float)) or (isinstance(age, str) and age.isdigit()) else 18
        self.money: float = float(money) if isinstance(money, (int, float)) or (isinstance(money, str) and money.isdigit()) else 0
        self.inventory: dict[str, list[Books]] | dict[None, None] = self._load_inventory()

    @staticmethod
    def _get_db_connection():
        conn = sqlite3.connect("library.db")
        conn.row_factory = sqlite3.Row
        return conn

    def _load_inventory(self) -> dict[str, list[Books]]:
        conn = Person._get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS inventory (
                person_name TEXT,
                book_id TEXT,
                PRIMARY KEY (person_name, book_id),
                FOREIGN KEY (book_id) REFERENCES books(book_id)
            )
        ''')
        conn.commit()

        inventory_data = {}
        cursor.execute('SELECT book_id FROM inventory WHERE person_name = ?', (self.name,))
        rows = cursor.fetchall()
        for row in rows:
            book = Books.get_book(row['book_id'])
            if book:
                if book.book_id not in inventory_data:
                    inventory_data[book.book_id] = []
                inventory_data[book.book_id].append(book)
        conn.close()
        return inventory_data

    def _save_inventory(self) -> None:
        conn = Person._get_db_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM inventory WHERE person_name = ?', (self.name,))
        for book_id in self.inventory.keys():
            for _ in self.inventory[book_id]:
                cursor.execute('INSERT OR REPLACE INTO inventory (person_name, book_id) VALUES (?, ?)', (self.name, book_id))
        conn.commit()
        conn.close()

    def status(self) -> None:
        print("-----------Persons-----------")
        print("-----------------------------")
        print(f"Name:      {self.name}")
        print(f"Age:       {self.age}")
        inventory_display = ", ".join([f"{book[0].title.capitalize()} x{len(self.inventory[book_id])}" for book_id, book in self.inventory.items()]) if any(self.inventory) else "Your Inventory is Empty"
        print(f"Inventory: {inventory_display}")
        print("-----------------------------")

    def borrow(self, book_id: str) -> None:
        book = Books.get_book(book_id)
        if book:
            if book.quantity > 0:
                if book_id not in self.inventory:
                    self.inventory[book_id] = []
                self.inventory[book_id].append(book)
                Books.update_quantity(book_id, book.quantity - 1, False)
                Books.add_to_rentee_ammount(book_id, False)
                self._save_inventory()
                print(f"\n{self.name} borrowed {book.title} successfully.\n")
            else:
                print(f"\nBook '{book.title.capitalize()}' by '{book.author.capitalize()}' is out of stock.\n")
        else:
            print(f"\nERROR: Invalid Book Id. Book Id '{book_id}' not found in database.\n")
        self.status()
        return None

if __name__ == '__main__':

    #Clean start database
    if Path("library.db").exists: os.remove("library.db")

    #Clean visual in cli
    clear = "cls" if sys.platform.startswith('win') else "clear"
    os.system(clear)

    Books.create_table()
    Books.initialise_from_csv("books.csv")
    person1 = Person("finn", 19, 150.00)
    Books.view(2)
    person1.borrow(2)
    Books.update_quantity(2,15)
    Books.add_to_rentee_ammount(1)
    Books.add_to_rentee_ammount(1)
    Books.add_to_rentee_ammount(1)
    Books.add_to_rentee_ammount(2)
    Books.add_to_rentee_ammount(3)
    Books.get_book_rank_by_stat_n_amount('amount_of_times_rented_desc',2)