#
# Qt compatibility shim for Lighthouse.
#
# Supports PyQt6 / PySide6 (Qt6), with legacy fallbacks for PyQt5 / PySide2.
# The rest of Lighthouse still uses a Qt5-style API surface, so we provide
# aliases for enums / methods that moved in Qt6.
#

QT_AVAILABLE = False

USING_PYQT6 = False
USING_PYQT5 = False
USING_PYSIDE6 = False
USING_PYSIDE2 = False

try:
    import ida_idaapi
    USING_IDA = True
except ImportError:
    USING_IDA = False

try:
    import binaryninjaui
    USING_NEW_BINJA = "qt_major_version" in binaryninjaui.__dict__ and binaryninjaui.qt_major_version == 6
    USING_OLD_BINJA = not(USING_NEW_BINJA)
except ImportError:
    USING_NEW_BINJA = False
    USING_OLD_BINJA = False

wrapinstance = None

def _install_qt6_compat():
    """Install Qt5-style compatibility aliases on top of Qt6 bindings."""

    # QAction lives in QtGui for Qt6, but Lighthouse imports it from QtWidgets.
    if not hasattr(QtWidgets, "QAction"):
        QtWidgets.QAction = QtGui.QAction

    # Provide exec_ aliases for code written against Qt5.
    for klass in (QtWidgets.QDialog, QtWidgets.QMenu, QtWidgets.QApplication):
        if hasattr(klass, 'exec') and not hasattr(klass, 'exec_'):
            klass.exec_ = klass.exec

    # Build a Qt5-style Qt namespace proxy.
    _Qt = QtCore.Qt
    class _QtCompat(object):
        pass
    QtCompat = _QtCompat()

    for name in dir(_Qt):
        if name.startswith('_'):
            continue
        try:
            setattr(QtCompat, name, getattr(_Qt, name))
        except Exception:
            pass

    _qt_aliases = {
        'AlignLeft': _Qt.AlignmentFlag.AlignLeft,
        'AlignRight': _Qt.AlignmentFlag.AlignRight,
        'AlignHCenter': _Qt.AlignmentFlag.AlignHCenter,
        'AlignTop': _Qt.AlignmentFlag.AlignTop,
        'AlignBottom': _Qt.AlignmentFlag.AlignBottom,
        'AlignVCenter': _Qt.AlignmentFlag.AlignVCenter,
        'AlignCenter': _Qt.AlignmentFlag.AlignCenter,
        'Horizontal': _Qt.Orientation.Horizontal,
        'Vertical': _Qt.Orientation.Vertical,
        'DisplayRole': _Qt.ItemDataRole.DisplayRole,
        'DecorationRole': _Qt.ItemDataRole.DecorationRole,
        'EditRole': _Qt.ItemDataRole.EditRole,
        'ToolTipRole': _Qt.ItemDataRole.ToolTipRole,
        'StatusTipRole': _Qt.ItemDataRole.StatusTipRole,
        'WhatsThisRole': _Qt.ItemDataRole.WhatsThisRole,
        'FontRole': _Qt.ItemDataRole.FontRole,
        'TextAlignmentRole': _Qt.ItemDataRole.TextAlignmentRole,
        'BackgroundRole': _Qt.ItemDataRole.BackgroundRole,
        'UserRole': _Qt.ItemDataRole.UserRole,
        'AccessibleDescriptionRole': _Qt.ItemDataRole.AccessibleDescriptionRole,
        'SizeHintRole': _Qt.ItemDataRole.SizeHintRole,
        'ItemIsEnabled': _Qt.ItemFlag.ItemIsEnabled,
        'ItemIsSelectable': _Qt.ItemFlag.ItemIsSelectable,
        'NoItemFlags': _Qt.ItemFlag.NoItemFlags,
        'PopupFocusReason': _Qt.FocusReason.PopupFocusReason,
        'StrongFocus': _Qt.FocusPolicy.StrongFocus,
        'CustomContextMenu': _Qt.ContextMenuPolicy.CustomContextMenu,
        'CaseInsensitive': _Qt.CaseSensitivity.CaseInsensitive,
        'AscendingOrder': _Qt.SortOrder.AscendingOrder,
        'DescendingOrder': _Qt.SortOrder.DescendingOrder,
        'SortOrder': _Qt.SortOrder,
        'ElideRight': _Qt.TextElideMode.ElideRight,
        'KeepAspectRatio': _Qt.AspectRatioMode.KeepAspectRatio,
        'SmoothTransformation': _Qt.TransformationMode.SmoothTransformation,
        'ScrollBarAlwaysOff': _Qt.ScrollBarPolicy.ScrollBarAlwaysOff,
        'WindowContextHelpButtonHint': _Qt.WindowType.WindowContextHelpButtonHint,
        'WindowCloseButtonHint': _Qt.WindowType.WindowCloseButtonHint,
        'MSWindowsFixedSizeDialogHint': _Qt.WindowType.MSWindowsFixedSizeDialogHint,
        'WA_Hover': _Qt.WidgetAttribute.WA_Hover,
        'WA_DontShowOnScreen': _Qt.WidgetAttribute.WA_DontShowOnScreen,
        'WA_TransparentForMouseEvents': _Qt.WidgetAttribute.WA_TransparentForMouseEvents,
        'RichText': _Qt.TextFormat.RichText,
        'LeftButton': _Qt.MouseButton.LeftButton,
        'RightDockWidgetArea': _Qt.DockWidgetArea.RightDockWidgetArea,
        'Key_Return': _Qt.Key.Key_Return,
        'Key_Enter': _Qt.Key.Key_Enter,
        'Key_Left': _Qt.Key.Key_Left,
        'Key_Right': _Qt.Key.Key_Right,
        'Key_Up': _Qt.Key.Key_Up,
        'Key_Down': _Qt.Key.Key_Down,
        'Key_H': _Qt.Key.Key_H,
        'Key_J': _Qt.Key.Key_J,
        'Key_K': _Qt.Key.Key_K,
        'Key_L': _Qt.Key.Key_L,
    }
    for name, value in _qt_aliases.items():
        setattr(QtCompat, name, value)
    QtCore.Qt = QtCompat

    # QEvent enum aliases.
    for name in ('HoverLeave', 'MouseButtonRelease', 'KeyPress'):
        if not hasattr(QtCore.QEvent, name) and hasattr(QtCore.QEvent.Type, name):
            setattr(QtCore.QEvent, name, getattr(QtCore.QEvent.Type, name))

    def _resolve_attr(root, path):
        obj = root
        for part in path.split('.'):
            if not hasattr(obj, part):
                return None
            obj = getattr(obj, part)
        return obj

    # Common widget enum aliases used throughout Lighthouse.
    enum_aliases = [
        (QtWidgets.QAbstractItemView, 'NoEditTriggers', 'EditTrigger.NoEditTriggers'),
        (QtWidgets.QAbstractItemView, 'SelectRows', 'SelectionBehavior.SelectRows'),
        (QtWidgets.QAbstractItemView, 'ScrollPerPixel', 'ScrollMode.ScrollPerPixel'),
        (QtWidgets.QAbstractItemView, 'PositionAtCenter', 'ScrollHint.PositionAtCenter'),
        (QtWidgets.QComboBox, 'AdjustToContentsOnFirstShow', 'SizeAdjustPolicy.AdjustToContentsOnFirstShow'),
        (QtWidgets.QHeaderView, 'Stretch', 'ResizeMode.Stretch'),
        (QtWidgets.QHeaderView, 'ResizeToContents', 'ResizeMode.ResizeToContents'),
        (QtWidgets.QHeaderView, 'Fixed', 'ResizeMode.Fixed'),
        (QtWidgets.QFileDialog, 'ExistingFile', 'FileMode.ExistingFile'),
        (QtWidgets.QFileDialog, 'ExistingFiles', 'FileMode.ExistingFiles'),
        (QtWidgets.QFileDialog, 'AnyFile', 'FileMode.AnyFile'),
        (QtWidgets.QSizePolicy, 'Expanding', 'Policy.Expanding'),
        (QtWidgets.QSizePolicy, 'Ignored', 'Policy.Ignored'),
        (QtWidgets.QSizePolicy, 'Minimum', 'Policy.Minimum'),
        (QtWidgets.QInputDialog, 'TextInput', 'InputMode.TextInput'),
        (QtWidgets.QPlainTextEdit, 'NoWrap', 'LineWrapMode.NoWrap'),
        (QtWidgets.QCompleter, 'PopupCompletion', 'CompletionMode.PopupCompletion'),
        (QtWidgets.QCompleter, 'CaseInsensitivelySortedModel', 'ModelSorting.CaseInsensitivelySortedModel'),
        (QtWidgets.QStyle, 'State_MouseOver', 'StateFlag.State_MouseOver'),
        (QtGui.QFont, 'Monospace', 'StyleHint.Monospace'),
        (QtGui.QFont, 'Bold', 'Weight.Bold'),
        (QtGui.QFont, 'ForceIntegerMetrics', 'StyleStrategy.ForceIntegerMetrics'),
        (QtGui.QTextCursor, 'MoveAnchor', 'MoveMode.MoveAnchor'),
        (QtGui.QTextCursor, 'KeepAnchor', 'MoveMode.KeepAnchor'),
        (QtGui.QIcon, 'Disabled', 'Mode.Disabled'),
        (QtGui.QPalette, 'Window', 'ColorRole.Window'),
        (QtGui.QPalette, 'WindowText', 'ColorRole.WindowText'),
        (QtGui.QPalette, 'Text', 'ColorRole.Text'),
    ]
    for target, name, value_path in enum_aliases:
        value = _resolve_attr(target, value_path)
        if value is not None and not hasattr(target, name):
            setattr(target, name, value)

# Prefer PyQt6 when available, then PySide6, then legacy fallbacks.
if USING_IDA:
    try:
        import PyQt6.QtGui as QtGui
        import PyQt6.QtCore as QtCore
        import PyQt6.QtWidgets as QtWidgets
        from PyQt6 import sip as _sip
        wrapinstance = _sip.wrapinstance
        QT_AVAILABLE = True
        USING_PYQT6 = True
        _install_qt6_compat()
    except ImportError:
        pass

if USING_IDA and not QT_AVAILABLE:
    try:
        import PySide6.QtGui as QtGui
        import PySide6.QtCore as QtCore
        import PySide6.QtWidgets as QtWidgets
        import shiboken6
        QtCore.pyqtSignal = QtCore.Signal
        QtCore.pyqtSlot = QtCore.Slot
        wrapinstance = shiboken6.wrapInstance
        QT_AVAILABLE = True
        USING_PYSIDE6 = True
        _install_qt6_compat()
    except ImportError:
        pass

if USING_IDA and not QT_AVAILABLE:
    try:
        import PyQt5.QtGui as QtGui
        import PyQt5.QtCore as QtCore
        import PyQt5.QtWidgets as QtWidgets
        import sip as _sip
        wrapinstance = _sip.wrapinstance
        QT_AVAILABLE = True
        USING_PYQT5 = True
    except ImportError:
        pass

if not QT_AVAILABLE and USING_OLD_BINJA:
    try:
        import PySide2.QtGui as QtGui
        import PySide2.QtCore as QtCore
        import PySide2.QtWidgets as QtWidgets
        import shiboken2
        QtCore.pyqtSignal = QtCore.Signal
        QtCore.pyqtSlot = QtCore.Slot
        wrapinstance = shiboken2.wrapInstance
        QT_AVAILABLE = True
        USING_PYSIDE2 = True
    except ImportError:
        pass

if not QT_AVAILABLE and USING_NEW_BINJA:
    try:
        import PySide6.QtGui as QtGui
        import PySide6.QtCore as QtCore
        import PySide6.QtWidgets as QtWidgets
        import shiboken6
        QtCore.pyqtSignal = QtCore.Signal
        QtCore.pyqtSlot = QtCore.Slot
        wrapinstance = shiboken6.wrapInstance
        QT_AVAILABLE = True
        USING_PYSIDE6 = True
        _install_qt6_compat()
    except ImportError:
        pass
