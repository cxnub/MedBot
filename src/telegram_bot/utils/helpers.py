from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def create_button_layout(buttons_data, max_buttons_per_row=2):
    """
    Create a button layout with specified maximum buttons per row.
    
    Args:
        buttons_data: List of tuples containing (button_text, callback_data)
        max_buttons_per_row: Maximum number of buttons per row (default: 2)
    
    Returns:
        List of lists of InlineKeyboardButton objects
    """
    keyboard = []
    row = []
    
    # check if the number of buttons is less than the maximum buttons per row
    if len(buttons_data) < max_buttons_per_row:
        max_buttons_per_row = len(buttons_data)
    
    for button_text, callback_data in buttons_data:
        row.append(InlineKeyboardButton(button_text, callback_data=callback_data))
        
        if len(row) >= max_buttons_per_row:
            keyboard.append(row)
            row = []
    
    # Add any remaining buttons in the last row
    if row:
        keyboard.append(row)
    
    return keyboard