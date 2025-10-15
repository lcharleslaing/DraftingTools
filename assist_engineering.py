import tkinter as tk
from tkinter import ttk
import os


class AssistEngineeringApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Assist Engineering")
        # Start maximized with standard window controls
        try:
            self.root.state('zoomed')
        except Exception:
            self.root.attributes('-zoomed', True)

        self.build_ui()

    def build_ui(self):
        container = ttk.Frame(self.root)
        container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        header = ttk.Label(container, text="Assist Engineering", font=('Arial', 20, 'bold'))
        header.pack(pady=(0, 10))

        sub = ttk.Label(
            container,
            text=(
                "This workspace will host tools to help Engineering.\n"
                "We'll add functions here as requirements are defined."
            ),
            font=('Arial', 12)
        )
        sub.pack(pady=(0, 20))

        # Placeholder main area
        placeholder = tk.Frame(container, bg='#e9f0fb', relief='groove', bd=2)
        placeholder.pack(fill=tk.BOTH, expand=True)

        msg = tk.Label(
            placeholder,
            text="Coming soon – add tasks, file helpers, and calculators here.",
            bg='#e9f0fb',
            fg='#2c3e50',
            font=('Arial', 12)
        )
        msg.pack(expand=True)

        # Footer with a Dashboard button
        footer = ttk.Frame(container)
        footer.pack(fill=tk.X, pady=(12, 0))
        dash_btn = ttk.Button(footer, text="Dashboard", command=self.return_to_dashboard)
        dash_btn.pack(side=tk.RIGHT)

    def return_to_dashboard(self):
        try:
            # Close this window; the Dashboard is launched manually by the user
            self.root.destroy()
        except Exception:
            self.root.quit()

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = AssistEngineeringApp()
    app.run()


