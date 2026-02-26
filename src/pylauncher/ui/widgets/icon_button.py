"""Reusable icon button with hover image swap."""

from __future__ import annotations

from typing import Callable, Optional

import customtkinter as ctk

from pylauncher.constants import TRANSPARENT, ICON_BUTTON_SIZE


class IconButton(ctk.CTkButton):
    """A transparent button that swaps between default and hover icons.

    Uses manual <Enter>/<Leave> binds to swap CTkImage on hover.
    """

    def __init__(
        self,
        master: ctk.CTkBaseClass,
        default_image: ctk.CTkImage,
        hover_image: ctk.CTkImage,
        command: Optional[Callable[[], None]] = None,
        size: int = ICON_BUTTON_SIZE,
        **kwargs,
    ) -> None:
        super().__init__(
            master,
            image=default_image,
            text="",
            width=size,
            height=size,
            fg_color=TRANSPARENT,
            hover=False,
            command=command,
            **kwargs,
        )
        self._default_image = default_image
        self._hover_image = hover_image
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)

    def _on_enter(self, event=None) -> None:
        self.configure(image=self._hover_image)

    def _on_leave(self, event=None) -> None:
        self.configure(image=self._default_image)

    def update_icons(
        self, default_image: ctk.CTkImage, hover_image: ctk.CTkImage
    ) -> None:
        """Replace both icons (e.g., toggling start/stop)."""
        self._default_image = default_image
        self._hover_image = hover_image
        self.configure(image=self._default_image)
