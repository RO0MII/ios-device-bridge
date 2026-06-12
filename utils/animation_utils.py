"""iOS-style animation helpers: spring curves, smooth transitions, combo anims."""

from PyQt6.QtCore import QPropertyAnimation, QEasingCurve, QPoint, QParallelAnimationGroup, QSequentialAnimationGroup
from PyQt6.QtWidgets import QWidget, QGraphicsOpacityEffect


def spring_curve() -> QEasingCurve:
    """iOS spring: fast start, overshoot 20%, settle back."""
    return QEasingCurve(QEasingCurve.Type.OutBack)


def ease_out_curve() -> QEasingCurve:
    """Smooth deceleration — iOS default."""
    return QEasingCurve(QEasingCurve.Type.OutCubic)


def ease_in_out_curve() -> QEasingCurve:
    """Smooth both ends — for combo transitions."""
    return QEasingCurve(QEasingCurve.Type.InOutCubic)


def animate_opacity(
    widget: QWidget,
    duration_ms: int = 300,
    start: float = 0.0,
    end: float = 1.0,
    easing: QEasingCurve | None = None,
) -> QPropertyAnimation:
    effect = QGraphicsOpacityEffect(widget)
    widget.setGraphicsEffect(effect)
    anim = QPropertyAnimation(effect, b"opacity")
    anim.setDuration(duration_ms)
    anim.setStartValue(start)
    anim.setEndValue(end)
    anim.setEasingCurve(easing or ease_out_curve())
    return anim


def animate_slide(
    widget: QWidget,
    duration_ms: int = 350,
    from_x: int = 0,
    to_x: int = 0,
    easing: QEasingCurve | None = None,
) -> QPropertyAnimation:
    pos = widget.pos()
    anim = QPropertyAnimation(widget, b"pos")
    anim.setDuration(duration_ms)
    anim.setStartValue(QPoint(pos.x() + from_x, pos.y()))
    anim.setEndValue(QPoint(pos.x() + to_x, pos.y()))
    anim.setEasingCurve(easing or ease_out_curve())
    return anim


def animate_push_in(widget: QWidget, duration_ms: int = 350) -> QPropertyAnimation:
    """Slide in from right with spring."""
    return animate_slide(widget, duration_ms, from_x=80, to_x=0, easing=spring_curve())


def animate_push_out(widget: QWidget, duration_ms: int = 280) -> QPropertyAnimation:
    """Slide out to left."""
    return animate_slide(widget, duration_ms, from_x=0, to_x=-60, easing=ease_out_curve())


def animate_pop_in(widget: QWidget, duration_ms: int = 350) -> QPropertyAnimation:
    """Slide in from left (back navigation)."""
    return animate_slide(widget, duration_ms, from_x=-80, to_x=0, easing=spring_curve())


def animate_staggered_reveal(
    cards: list[QWidget],
    total_duration_ms: int = 500,
) -> QParallelAnimationGroup:
    """iOS-style staggered card reveal — all fade + subtle slide simultaneously."""
    group = QParallelAnimationGroup()
    for i, card in enumerate(cards):
        effect = QGraphicsOpacityEffect(card)
        card.setGraphicsEffect(effect)
        anim = QPropertyAnimation(effect, b"opacity")
        anim.setDuration(total_duration_ms)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.setEasingCurve(ease_out_curve())
        group.addAnimation(anim)
    return group


def animate_spring_bounce(widget: QWidget, duration_ms: int = 400) -> QPropertyAnimation:
    """iOS spring bounce on value change — subtle scale via geometry."""
    geo = widget.geometry()
    anim = QPropertyAnimation(widget, b"geometry")
    anim.setDuration(duration_ms)
    anim.setKeyValueAt(0, geo.adjusted(4, 4, -4, -4))
    anim.setKeyValueAt(0.5, geo.adjusted(-1, -1, 1, 1))
    anim.setEndValue(geo)
    anim.setEasingCurve(spring_curve())
    return anim


def animate_color_transition(
    widget: QWidget,
    duration_ms: int = 250,
) -> QPropertyAnimation:
    """Opacity pulse for color change (fade out/in trick)."""
    effect = QGraphicsOpacityEffect(widget)
    widget.setGraphicsEffect(effect)
    anim = QPropertyAnimation(effect, b"opacity")
    anim.setDuration(duration_ms)
    anim.setKeyValueAt(0, 1.0)
    anim.setKeyValueAt(0.3, 0.3)
    anim.setKeyValueAt(0.7, 1.3)
    anim.setEndValue(1.0)
    anim.setEasingCurve(ease_out_curve())
    return anim


def animate_breathing(
    widget: QWidget,
    duration_ms: int = 2000,
) -> QPropertyAnimation:
    """Subtle breathing pulse for active status indicators."""
    effect = QGraphicsOpacityEffect(widget)
    widget.setGraphicsEffect(effect)
    anim = QPropertyAnimation(effect, b"opacity")
    anim.setDuration(duration_ms)
    anim.setLoopCount(-1)
    anim.setKeyValueAt(0, 1.0)
    anim.setKeyValueAt(0.5, 0.6)
    anim.setEndValue(1.0)
    anim.setEasingCurve(ease_in_out_curve())
    return anim
