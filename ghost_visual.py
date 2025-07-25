from tkinter import scrolledtext
import tkinter as tk
import subprocess
import threading


class GhostVisual:
    def __init__(self, root, assistant=None):
        self.root = root
        self.root.title("Osmanli AI - Ghost Visual")
        self.assistant = assistant

        self.title_label = tk.Label(
            root,
            text="Osmanli AI - Ghost Visual",
            font=("Arial", 16),
            bg="#2E3440",
            fg="#D8DEE9",
        )
        self.title_label.pack(pady=10)

        self.text_area = scrolledtext.ScrolledText(
            root,
            wrap=tk.WORD,
            bg="#2E3440",
            fg="#D8DEE9",
            insertbackground="#D8DEE9",
            font=("Consolas", 12),
        )
        self.text_area.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        self.text_area.configure(state="disabled", bd=0)

        self.entry = tk.Entry(
            root,
            bg="#2E3440",
            fg="#D8DEE9",
            insertbackground="#D8DEE9",
            font=("Consolas", 12),
            bd=0,
        )
        self.entry.pack(padx=10, pady=5, fill=tk.X, expand=False)
        self.entry.bind("<Return>", self.handle_input)

    def handle_input(self, event):
        user_input = self.entry.get()
        self.entry.delete(0, tk.END)  # Clear the input field immediately
        self.update_text_area(f"You: {user_input}\n")  # Echo user input

        if user_input.startswith("!"):
            command = user_input[1:]
            self.update_text_area(f"Processing command: {command}\n")
            threading.Thread(target=self.run_command, args=(command,)).start()
        elif user_input.lower() == "launch neovim":
            self.update_text_area("Launching Neovim in a new terminal...\n")
            threading.Thread(target=self.launch_neovim).start()
        elif self.assistant:
            # Send the input to the assistant and display the response
            self.update_text_area("Assistant is thinking...\n")
            response = self.assistant.get_response(
                user_input
            )  # This method needs to be implemented in the assistant
            self.update_text_area(f"Assistant: {response}\n")
        else:
            self.update_text_area(f"Command not recognized: {user_input}\n")

    def run_command(self, command):
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            shell=True,
            text=True,
            bufsize=1,
            universal_newlines=True,
        )

        for line in process.stdout:
            self.update_text_area(line)

        process.stdout.close()
        process.wait()

    def update_text_area(self, text):
        self.text_area.configure(state="normal")
        self.text_area.insert(tk.END, text)
        self.text_area.configure(state="disabled")
        self.text_area.see(tk.END)

    def launch_neovim(self):
        try:
            # Attempt to launch Neovim in a new gnome-terminal window
            subprocess.Popen(["gnome-terminal", "--", "nvim"])
        except FileNotFoundError:
            self.update_text_area(
                "Error: gnome-terminal not found. Please ensure it's installed or modify the launch command.\n"
            )
        except Exception as e:
            self.update_text_area(f"Error launching Neovim: {e}\n")


def run_ghost_visual(assistant=None):
    root = tk.Tk()
    root.geometry("800x600")  # Set initial window size
    root.configure(bg="#2E3440")
    GhostVisual(root, assistant)
    root.mainloop()


if __name__ == "__main__":
    run_ghost_visual()
