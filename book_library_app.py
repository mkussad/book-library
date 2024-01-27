import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
import sqlite3
import csv

class BookLibraryApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Book Library")

        # Connect to SQLite database
        self.conn = sqlite3.connect("book_library.db")
        self.create_table()

        self.page_size = 10
        self.current_page = 1
        self.total_pages = 1

        self.create_widgets()

        # Handle window close event
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def create_table(self):
        # Create or ensure the existence of the 'books' table in the database
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS books (
                    id INTEGER PRIMARY KEY,
                    title TEXT,
                    author TEXT,
                    status TEXT
                )
            ''')
            self.conn.commit()
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Error creating table: {str(e)}")

    def create_widgets(self):
        # Main Frame
        main_frame = ttk.Frame(self.root)
        main_frame.grid(row=0, column=0, sticky="nsew")

        # Treeview (Table)
        columns = ("Title", "Author", "Read")
        self.tree = ttk.Treeview(main_frame, columns=columns, show="headings")
        for col in columns:
            self.tree.heading(col, text=col)
        self.tree.grid(row=0, column=0, columnspan=3, padx=10, pady=5, sticky="nsew")

        # Buttons Frame
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.grid(row=1, column=0, columnspan=3, pady=10, sticky="nsew")

        # Buttons
        add_button = ttk.Button(buttons_frame, text="Add Book", command=self.show_add_book_dialog)
        add_button.grid(row=0, column=0, padx=5)

        mark_read_button = ttk.Button(buttons_frame, text="Mark as Read/Unread", command=self.mark_as_read)
        mark_read_button.grid(row=0, column=1, padx=5)

        edit_button = ttk.Button(buttons_frame, text="Edit Book", command=self.edit_book)
        edit_button.grid(row=0, column=2, padx=5)

        delete_button = ttk.Button(buttons_frame, text="Delete Book", command=self.delete_book)
        delete_button.grid(row=0, column=3, padx=5)

        export_button = ttk.Button(buttons_frame, text="Export to CSV", command=self.export_to_csv)
        export_button.grid(row=0, column=4, padx=5)

        # Pagination Frame
        pagination_frame = ttk.Frame(main_frame)
        pagination_frame.grid(row=2, column=0, columnspan=3, pady=5, sticky="nsew")

        # Pagination Buttons
        self.prev_button = ttk.Button(pagination_frame, text="Previous Page", command=self.prev_page)
        self.prev_button.grid(row=0, column=0, padx=5)

        self.next_button = ttk.Button(pagination_frame, text="Next Page", command=self.next_page)
        self.next_button.grid(row=0, column=1, padx=5)

        # Load books from the database
        self.load_books()

        # Configure weights for grid resizing
        for i in range(3):  # Three columns
            main_frame.columnconfigure(i, weight=1)

        for i in range(3):  # Three rows
            main_frame.rowconfigure(i, weight=1)

    def show_add_book_dialog(self):
        # Method for displaying a dialog to add a new book
        while True:
            title = simpledialog.askstring("Book Details", "Enter the book title:")
            if title and title.strip():
                author = simpledialog.askstring("Book Details", f"Enter the author of '{title}':")
                if author and author.strip():
                    self.add_book_to_db(title.strip(), author.strip())
                    self.load_books()
                    messagebox.showinfo("Success", "Book added successfully!")
                    break  # Break out of the loop if both title and author are provided
                else:
                    retry_author = messagebox.askretrycancel("Missing Information", "Author cannot be empty. Do you want to try again?")
                    if not retry_author:
                        break  # Break out of the loop if the user chooses not to retry
            else:
                retry_title = messagebox.askretrycancel("Missing Information", "Title cannot be empty. Do you want to try again?")
                if not retry_title:
                    break  # Break out of the loop if the user chooses not to retry

    def load_books(self):
        # Method for loading books from the database and updating the UI
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Retrieve books for the current page from the database
        offset = (self.current_page - 1) * self.page_size
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, title, author, status FROM books LIMIT ? OFFSET ?", (self.page_size, offset))
        books = cursor.fetchall()

        # Populate the table with book data
        for book in books:
            self.tree.insert("", "end", values=(book[1], book[2], book[3]))

        # Update pagination information
        self.update_pagination_info()
    
    def update_pagination_info(self):
        # Update information about the current page and disable/enable pagination buttons
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM books")
        total_books = cursor.fetchone()[0]

        self.total_pages = (total_books + self.page_size - 1) // self.page_size
        current_page_info = f"Page {self.current_page} of {self.total_pages}"
        self.tree.heading("#0", text=current_page_info)

        # Disable/Enable pagination buttons based on current page
        self.prev_button["state"] = "normal" if self.current_page > 1 else "disabled"
        self.next_button["state"] = "normal" if self.current_page < self.total_pages else "disabled"

    def next_page(self):
        # Navigate to the next page and load books
        if self.current_page < self.total_pages:
            self.current_page += 1
            self.load_books()

    def prev_page(self):
        # Navigate to the previous page and load books
        if self.current_page > 1:
            self.current_page -= 1
            self.load_books()

    def add_book_to_db(self, title, author):
        # Add a new book to the database
        try:
            if title and title.strip() and author and author.strip():
                cursor = self.conn.cursor()
                cursor.execute("INSERT INTO books (title, author, status) VALUES (?, ?, 'unread')", (title.strip(), author.strip()))
                self.conn.commit()
            else:
                messagebox.showwarning("Missing Information", "Both title and author are required. Please enter both.")
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Error adding book to database: {str(e)}")

    def get_book_id(self, selected_item):
        # Get the ID of the selected book from the Treeview
        selected_title = self.tree.item(selected_item, "values")[0]
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, title, author, status FROM books")
        books = cursor.fetchall()
        for book in books:
            if book[1] == selected_title:  # Check if title matches
                selected_id = book[0]  # Retrieve the corresponding ID
                break
        return int(selected_id)

    def mark_as_read(self):
        # Mark a book as read or unread
        try:
            selected_item = self.tree.selection()
            if selected_item:
                book_id = self.get_book_id(selected_item)
                if book_id is not None:
                    cursor = self.conn.cursor()

                    # Retrieve the current status of the selected book
                    cursor.execute("SELECT status FROM books WHERE id=?", (book_id,))
                    current_status = cursor.fetchone()[0]

                    # Toggle between 'read' and 'unread'
                    new_status = 'unread' if current_status == 'read' else 'read'

                    # Update the status of the selected book
                    cursor.execute("UPDATE books SET status=? WHERE id=?", (new_status, book_id))
                    self.conn.commit()

                    # Reload books to update the table
                    self.load_books()
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Error marking book as read: {str(e)}")

    def edit_book(self):
        # Edit the details of an existing book
        selected_item = self.tree.selection()
        if selected_item:
            book_id = self.get_book_id(selected_item)
            if book_id is not None:
                cursor = self.conn.cursor()
                cursor.execute("SELECT title, author FROM books WHERE id=?", (book_id,))
                book_info = cursor.fetchone()

                new_title = simpledialog.askstring("Edit Book", "Enter the updated title:", initialvalue=book_info[0])
                if new_title and new_title.strip():
                    new_author = simpledialog.askstring("Edit Book", f"Enter the updated author of '{new_title}':", initialvalue=book_info[1])
                    if new_author and new_author.strip():
                        cursor.execute("UPDATE books SET title=?, author=? WHERE id=?", (new_title.strip(), new_author.strip(), book_id))
                        self.conn.commit()
                        self.load_books()
                    else:
                        messagebox.showwarning("Missing Information", "Author cannot be empty. Please enter the author.")
                else:
                    messagebox.showwarning("Missing Information", "Title cannot be empty. Please enter the title.")

    def delete_book(self):
        # Delete a book from the database
        try:
            selected_item = self.tree.selection()
            if selected_item:
                book_id = self.get_book_id(selected_item)
                if book_id is not None:
                    confirmation = messagebox.askyesno("Confirm Deletion", "Are you sure you want to delete this book?")
                    if confirmation:
                        cursor = self.conn.cursor()
                        cursor.execute("DELETE FROM books WHERE id=?", (book_id,))
                        self.conn.commit()
                        self.load_books()
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Error deleting book from database: {str(e)}")

    def export_to_csv(self):
        # Export the book library to a CSV file
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT title, author, status FROM books")
            books = cursor.fetchall()

            # Ask the user for the CSV file name
            file_name = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])

            if file_name:
                with open(file_name, mode='w', newline='', encoding='utf-8') as csv_file:
                    csv_writer = csv.writer(csv_file)
                    # Write header
                    csv_writer.writerow(["Title", "Author", "Status"])
                    # Write data
                    csv_writer.writerows(books)

                messagebox.showinfo("Export Successful", f"Book library exported to {file_name} successfully!")
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Error exporting to CSV: {str(e)}")
        except Exception as e:
            messagebox.showerror("Export Error", f"Error exporting to CSV: {str(e)}")

    def on_close(self):
        # Handle the window close event
        self.conn.close()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = BookLibraryApp(root)
    root.mainloop()

