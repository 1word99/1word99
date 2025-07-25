from tkinter import ttk
import tkinter as tk
from osmanli_ai.core.user_profile import UserProfile
from pathlib import Path


class OsmanliAIApp(tk.Tk):
    def __init__(self, user_profile: UserProfile):
        super().__init__()
        self.user_profile = user_profile
        self.title("Osmanli AI - The Ottoman Experience")
        self.geometry("800x600")
        self.configure_styles()
        self.create_widgets()

    def configure_styles(self):
        """Configure Ottoman-themed styles."""
        style = ttk.Style()
        style.theme_use("clam")

        style.configure(
            "TFrame",
            background="#f0e6d9",  # Light beige background
            relief="groove",
            borderwidth=2,
        )

        style.configure(
            "TButton",
            background="#8b795e",  # Dark brown button
            foreground="white",
            font=("Times New Roman", 12),
            padding=5,
        )

        style.configure(
            "TLabel",
            background="#f0e6d9",
            foreground="#332a22",  # Dark brown text
            font=("Times New Roman", 14),
        )

        style.configure(
            "TEntry",
            fieldbackground="white",
            background="#d2b48c",  # Light brown background
            foreground="#332a22",
            font=("Times New Roman", 12),
        )

    def create_widgets(self):
        """Create the main widgets for the application."""
        # Main frame
        main_frame = ttk.Frame(self, padding="10")
        main_frame.grid(row=0, column=0, sticky="nsew")

        # Title label
        title_label = ttk.Label(
            main_frame,
            text="Welcome to Osmanli AI",
            font=("Times New Roman", 24, "bold"),
        )
        title_label.grid(row=0, column=0, columnspan=2, pady=10)

        # User profile frame
        profile_frame = ttk.Frame(main_frame, padding="10")
        profile_frame.grid(row=1, column=0, sticky="nsew")

        profile_label = ttk.Label(
            profile_frame, text="User Profile", font=("Times New Roman", 16, "bold")
        )
        profile_label.grid(row=0, column=0, pady=5)

        profile_name_label = ttk.Label(
            profile_frame, text=f"Name: {self.user_profile.get('name', 'Guest')}"
        )
        profile_name_label.grid(row=1, column=0, pady=5)

        profile_preferences_label = ttk.Label(
            profile_frame,
            text=f"Preferences: {self.user_profile.get('preferences', {})}",
        )
        profile_preferences_label.grid(row=2, column=0, pady=5)

        # Quests and achievements frame
        quests_frame = ttk.Frame(main_frame, padding="10")
        quests_frame.grid(row=1, column=1, sticky="nsew")

        quests_label = ttk.Label(
            quests_frame,
            text="Quests and Achievements",
            font=("Times New Roman", 16, "bold"),
        )
        quests_label.grid(row=0, column=0, pady=5)

        quests_listbox = tk.Listbox(
            quests_frame, height=10, font=("Times New Roman", 12)
        )
        quests_listbox.grid(row=1, column=0, pady=5)

        # Sample quests
        quests = [
            "Complete your first coding project",
            "Analyze market trends",
            "Optimize a component",
            "Earn 100 gold",
        ]

        for quest in quests:
            quests_listbox.insert(tk.END, quest)

        # Interactive tutorial frame
        tutorial_frame = ttk.Frame(main_frame, padding="10")
        tutorial_frame.grid(row=2, column=0, columnspan=2, sticky="nsew")

        tutorial_label = ttk.Label(
            tutorial_frame,
            text="Interactive Tutorial",
            font=("Times New Roman", 16, "bold"),
        )
        tutorial_label.grid(row=0, column=0, pady=5)

        tutorial_text = tk.Text(
            tutorial_frame, height=10, font=("Times New Roman", 12), wrap="word"
        )
        tutorial_text.grid(row=1, column=0, pady=5)

        tutorial_text.insert(
            tk.END,
            "Welcome to the interactive tutorial!\nFollow the steps below to get started with Osmanli AI.",
        )

        # Sample tutorial steps
        tutorial_steps = [
            "Step 1: Create a new project",
            "Step 2: Write your first line of code",
            "Step 3: Analyze your code for issues",
            "Step 4: Optimize your code",
            "Step 5: Share your project with the community",
        ]

        for step in tutorial_steps:
            tutorial_text.insert(tk.END, f"\n{step}")


if __name__ == "__main__":
    # Create a dummy user profile for demonstration purposes
    dummy_profile = UserProfile("dummy_user", Path("user_profiles"))
    dummy_profile.set("name", "Osman the Great")
    dummy_profile.update_preferences({"theme": "Ottoman", "notifications": True})

    app = OsmanliAIApp(dummy_profile)
    app.mainloop()
