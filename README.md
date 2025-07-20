# Library Management System (AI-Powered CLI)

This project is a sophisticated, command-line interface (CLI) for managing a library database, powered by the Mistral AI platform. Instead of writing complex SQL queries, the librarian interacts with the system using natural language. An AI assistant interprets these requests, asks clarifying questions, and uses a secure set of tools to interact with the database, handling everything from book recommendations to rental management.

## Features

-   **Natural Language Interface**: Manage the entire library by talking to an AI in plain English.
-   **Intelligent Recommendations**: The AI can infer user intent. Asking for "something techy" won't just search for the keyword; it will fetch the book list and use its own knowledge to recommend relevant titles like "The Silicon Soul" or "Neuromancer".
-   **Complex Queries Made Simple**: Ask complex questions like "Which books does John Doe have rented out right now?" and be amazed as it gets you exactly what you want.
-   **Safe, High-Level Functions**: The most common tasks—renting a book, returning a book, adding a user—are handled by dedicated, safe Python functions, minimizing direct SQL execution.
-   **Secure Operations**: Potentially destructive raw SQL queries are fire-walled behind a password prompt, preventing accidental changes.
-   **Persistent Logging**: All function calls triggered by the AI are logged to `executed_commands.log` for easy review and debugging.

## Technology Stack

-   **Python 3**
-   **AI Model**: Mistral (`mistral-large-latest`)
-   **Database**: SQLite 3

## Setup and Installation

Follow these steps to get the project running locally.

**1. Clone the Repository**
```bash
git clone https://github.com/bilalammar/library-management-system.git
cd library-management-system
```

**2. Install Dependencies**
```bash
pip install -r requirements.txt
```

**3. Create the Environment File**

Create a file named `.env` in the root of the project directory. This file will hold your Mistral API key. Add the following line to it:

```
MISTRAL_KEY="your_mistral_api_key_here"
```

**BONUS**
Use the SQL dump file `books.sql` to fill the database with dummy data to test it out
```
sqlite3 library.db < books.sql
```

## Usage

Once the setup is complete, run the main application script:

```bash
python main.py
```

The application will initialize, and you can start interacting with the AI assistant.

### Example Interactions

**Example 1: Intelligent Recommendation**
```
<<YOU>> I need a good sci-fi book for a gift.
<<BOT>> Of course. Let me see what we have in the catalog.
... (The AI calls fetch_data('SELECT title FROM books')) ...
<<BOT>> Based on your request for sci-fi, I can recommend a few titles from our collection. We have classics like "Dune" and "Neuromancer", or more modern works like "Project Hail Mary" and "Children of Time". Do any of those sound interesting?
```

**Example 2: Complex Query (JOIN)**
```
<<YOU>> Can you tell me who has the book 'The Martian' rented out?
<<BOT>> One moment, let me check the rental records.
... (The AI calls fetch_data with a JOIN query) ...
<<BOT>> According to our records, 'The Martian' is currently rented out by Jane Smith (user_id: user_f4b5c8d9).
```

**Example 3: High-Level Workflow (Renting a Book)**
```
<<YOU>> I need to process a new rental. John Appleseed is renting 'Hyperion'.
<<BOT>> Understood. To process the rental, I need the user_id for John Appleseed and the book_id for 'Hyperion'.
... (You provide the IDs) ...
<<BOT>> Thank you. I am processing the rental for user 'user_a1b2c3d4' and book 'book_d8c6b4a1'.
... (The AI calls get_current_date, then add_rental) ...
<<BOT>> The rental has been successfully processed. The rental ID is 'rent_e5f6a1b2'.
```