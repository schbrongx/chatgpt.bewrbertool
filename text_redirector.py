## text_redirector.py

import tkinter as tk

class TextRedirector:
    """
    A class that redirects the output of sys.stdout or sys.stderr to a tkinter Text widget.
    
    This class is useful when you want to capture printed output and display it in a 
    GUI text widget, such as a log or console area in a tkinter application.
    
    Attributes:
    ----------
    text_widget : tkinter.Text
        The Text widget where the output (stdout or stderr) will be displayed.
    """

    def __init__(self, text_widget):
        """
        Initialize the TextRedirector instance.
        
        Parameters:
        ----------
        text_widget : tkinter.Text
            A tkinter Text widget that will display the redirected text output.
        """
        self.text_widget = text_widget

    def write(self, message):
        """
        Insert a message into the tkinter Text widget.
        
        This method is called when text is written to sys.stdout or sys.stderr. 
        The message is inserted into the provided tkinter Text widget, and the widget is 
        automatically scrolled to the end so that the latest output is always visible.
        
        Parameters:
        ----------
        message : str
            The message to be displayed in the Text widget (i.e., the printed text).
        """
        # Insert the message into the Text widget at the end (tk.END)
        self.text_widget.insert(tk.END, message)
        
        # Ensure the Text widget automatically scrolls to the latest output
        self.text_widget.see(tk.END)

    def flush(self):
        """
        Flush the output buffer.
        
        This method is typically needed in interactive environments where 
        buffering might be used. It ensures that any remaining buffered data is 
        written out to the widget. For most use cases, this method will be a no-op.
        
        Note:
        ----
        This method is included to conform with file-like object requirements 
        and may not need to perform any action in this context.
        """
        pass
