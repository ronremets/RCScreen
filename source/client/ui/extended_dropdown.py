"""
A dropdown that can show multiple batches of information.
"""
__author__ = "Ron Remets"

from kivy.clock import Clock
from kivy.properties import ObjectProperty, NumericProperty, ListProperty
from kivy.uix.button import Button
from kivy.uix.dropdown import DropDown

from kivy.core.window import Window


class ExtendedDropdown(DropDown):
    """
    A dropdown that can show multiple batches of information.
    """
    _batches = ListProperty()
    _current_batch_index = NumericProperty(0)
    items = ListProperty()
    max_batch_height = NumericProperty(1)

    def on_items(self, instance, items):
        """
        When items change, update the dropdown.
        :param instance: The instance that changed batches
        :param items: The new items
        """
        print(f"new items: {items}\n instance: {instance}")
        self._current_batch_index = 0
        batches = []
        if len(items) > 0:
            for i in range(self.max_batch_height,
                           len(items),
                           self.max_batch_height):
                batches.append(items[i - self.max_batch_height:i])
            batches.append(items[
                max(len(items) - (len(items) % self.max_batch_height) - 1, 0):])
        self._batches = batches
        self._refresh()

    def _select_item(self, button):
        """
        Select an item from the batch
        :param button: The button of the item
        """
        self.select(button.text)

    def _refresh(self):
        """
        Refresh the items in the dropdown to the items of the current
        batch.
        """
        self.clear_widgets()
        if len(self._batches) > 0:
            batch = self._batches[self._current_batch_index]
            batch += "hello world!!!!"
            for item in batch:
                self.add_widget(Button(size_hint_y=None,
                                       height=Window.height / len(batch),
                                       text=item,
                                       on_release=self._select_item))
            print(f"Changed batch to: {batch}")
            print(f"Dropdown widgets: {self.container.children}")

    def change_to_next_batch(self):
        """
        Change the elements in the dropdown to the elements of the next
        batch
        """
        print(f"ON CHANGE: batches: {self._batches}\nindex: {self._current_batch_index}")
        self._current_batch_index = ((self._current_batch_index + 1)
                                     % len(self._batches))
        self._refresh()

    def open(self, widget):
        """
        Open the dropdown and allow to select elements from batches
        """
        print(self)
        print(
            f"ON OPEN: batches: {self._batches}\nindex: {self._current_batch_index}")
        self._refresh()
        super().open(widget)
