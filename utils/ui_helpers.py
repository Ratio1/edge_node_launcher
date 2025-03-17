"""UI helper utilities for thread-safe UI operations."""

from PyQt5.QtCore import QObject, pyqtSignal, QMetaObject, Qt, Q_ARG, QVariant


class ThreadSafeUIUpdater(QObject):
    """Helper class for thread-safe UI updates.
    
    This class provides a way to safely update UI elements from non-UI threads
    by using Qt's signal/slot mechanism to ensure updates happen on the main thread.
    """
    
    # Signal to close a dialog
    close_dialog_signal = pyqtSignal(QObject)
    
    # Signal to update a dialog message
    update_message_signal = pyqtSignal(QObject, str)
    
    # Signal to update progress
    update_progress_signal = pyqtSignal(QObject, int)
    
    # Signal for generic method invocation
    invoke_method_signal = pyqtSignal(QObject, str, object)
    
    def __init__(self):
        """Initialize the UI updater."""
        super().__init__()
        
        # Connect signals to slots
        self.close_dialog_signal.connect(self._close_dialog)
        self.update_message_signal.connect(self._update_message)
        self.update_progress_signal.connect(self._update_progress)
        self.invoke_method_signal.connect(self._invoke_method)
    
    @staticmethod
    def _close_dialog(dialog):
        """Close a dialog safely on the main thread.
        
        Args:
            dialog: The dialog to close
        """
        if dialog and hasattr(dialog, 'close'):
            dialog.close()
    
    @staticmethod
    def _update_message(dialog, message):
        """Update a dialog message safely on the main thread.
        
        Args:
            dialog: The dialog to update
            message: The new message
        """
        if dialog and hasattr(dialog, 'set_message'):
            dialog.set_message(message)
    
    @staticmethod
    def _update_progress(dialog, progress):
        """Update a dialog progress safely on the main thread.
        
        Args:
            dialog: The dialog to update
            progress: The new progress value
        """
        if dialog and hasattr(dialog, 'update_progress'):
            dialog.update_progress(progress)
    
    @staticmethod
    def _invoke_method(obj, method_name, args):
        """Invoke a method on an object safely on the main thread.
        
        Args:
            obj: The object to invoke the method on
            method_name: The name of the method to invoke
            args: The arguments to pass to the method
        """
        if obj and hasattr(obj, method_name):
            method = getattr(obj, method_name)
            if callable(method):
                if isinstance(args, (list, tuple)):
                    method(*args)
                else:
                    method(args)
    
    def safe_close_dialog(self, dialog):
        """Close a dialog safely from any thread.
        
        Args:
            dialog: The dialog to close
        """
        self.close_dialog_signal.emit(dialog)
    
    def safe_update_message(self, dialog, message):
        """Update a dialog message safely from any thread.
        
        Args:
            dialog: The dialog to update
            message: The new message
        """
        self.update_message_signal.emit(dialog, message)
    
    def safe_update_progress(self, dialog, progress):
        """Update a dialog progress safely from any thread.
        
        Args:
            dialog: The dialog to update
            progress: The new progress value
        """
        self.update_progress_signal.emit(dialog, progress)
    
    def safe_invoke_method(self, obj, method_name, args):
        """Invoke a method on an object safely from any thread.
        
        Args:
            obj: The object to invoke the method on
            method_name: The name of the method to invoke
            args: The arguments to pass to the method
        """
        self.invoke_method_signal.emit(obj, method_name, args)


# Global instance for convenience
ui_updater = ThreadSafeUIUpdater()
