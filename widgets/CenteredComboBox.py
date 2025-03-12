from PyQt5.QtWidgets import QComboBox, QStyledItemDelegate
from PyQt5.QtCore import Qt, QObject, QEvent, QTimer
from PyQt5.QtGui import QFontMetrics

class ClickToOpenFilter(QObject):
    def __init__(self, combo):
        super().__init__(combo)
        self.combo = combo

    def eventFilter(self, obj, event):
        if obj == self.combo.lineEdit() and event.type() == QEvent.MouseButtonPress:
            self.combo.showPopup()
            return True
        return super().eventFilter(obj, event)

class CenteredComboBox(QComboBox):
    """A QComboBox that centers both the dropdown items and the selected item."""

    def __init__(self, parent=None):
        super().__init__(parent)
        # Set up a delegate to center the items in the view
        delegate = QStyledItemDelegate(self)
        self.setItemDelegate(delegate)

        # Make editable to get the line edit for centering
        self.setEditable(True)

        # Disable editing by setting read-only
        self.lineEdit().setReadOnly(True)

        # Center the text in the line edit
        self.lineEdit().setAlignment(Qt.AlignCenter)

        # Make the line edit look like a non-editable combo box
        self.lineEdit().setFrame(False)
        self.lineEdit().setStyleSheet("background:transparent;")
        self.lineEdit().installEventFilter(ClickToOpenFilter(self))
        # Disable all text interactions:
        self.lineEdit().setFocusPolicy(Qt.NoFocus)


        # (Optional) Change the cursor so it doesn’t look like an I-beam:
        self.lineEdit().setCursor(Qt.ArrowCursor)

        # Set combobox styles
        self.setStyleSheet("""
            QComboBox {
                combobox-popup: 1;
                background: transparent;
                border-radius: 15px;
            }
        """)
        self.view().parentWidget().setStyleSheet("background: transparent;")
        # Ensure combo box popup items are centered as well
        for i in range(self.count()):
            self.setItemData(i, Qt.AlignCenter, Qt.TextAlignmentRole)

    def addItem(self, text, userData=None):
        """Override addItem to ensure new items are center-aligned"""
        super().addItem(text, userData)
        self.setItemData(self.count() - 1, Qt.AlignCenter, Qt.TextAlignmentRole)

    def insertItem(self, index, text, userData=None):
        """Override insertItem to ensure new items are center-aligned"""
        super().insertItem(index, text, userData)
        self.setItemData(index, Qt.AlignCenter, Qt.TextAlignmentRole)

    def showPopup(self):
        """Override showPopup to ensure all items are center-aligned and have rounded corners"""
        for i in range(self.count()):
            self.setItemData(i, Qt.AlignCenter, Qt.TextAlignmentRole)

        # Apply styling to the view
        self.view().setStyleSheet("""
            QListView {
                border: 1px solid #555;
                border-radius: 6px;
                background-color: #1E293B;
                outline: 10px;
                padding: 14px;
            }
            
            QListView::item {
                border-radius: 6px;
                padding: 4px;
                margin: 2px;
            }
            
            QListView::item:selected {
                background-color: #2a82da;
                color: white;
            }
        QComboBox QAbstractItemView::item {
            text-align: center;
        }
        """)

        # Set window flags to remove frame and shadow
        self.view().window().setWindowFlags(Qt.Popup | Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint)

        # Make the background translucent
        self.view().window().setAttribute(Qt.WA_TranslucentBackground)

        super().showPopup()