from PyQt5.QtWidgets import QMessageBox

def show_critical_message(parent, title, message):
    """
    Display a critical message box.

    Parameters:
    parent (QWidget): The parent widget.
    title (str): The title of the message box.
    message (str): The message to display.
    """
    QMessageBox.critical(parent, title, message)