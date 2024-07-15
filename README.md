# Midtrans Telegram Bot

**Making a QRIS Payment Bot in Python using Midtrans API**

A simple Telegram bot that assists you in managing your QRIS payment activities using Midtrans API.

## Features

- **Add Products to Cart**: Easily add products to your shopping cart.
- **View Cart**: Display a list of all items in your cart.
- **Checkout**: Generate a QRIS code for payment.
- **Check Payment Status**: Verify the payment status of your order.
- **View Pending Orders**: Display a list of pending orders.
- **Send Transaction Logs**: Send a log of today's transactions.

## Packages Used

- **telethon**: To interact with the Telegram API.
- **requests**: To make HTTP requests to the Midtrans API.
- **pytz**: To handle timezone information.

## Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/christoaaron/Midtrans-Telegram-Bot.git
   ```

2. Navigate to the project directory:
   ```bash
   cd QRISPayBot
   ```
3. Install the required packages:
   ```bash
   pip install telethon requests pytz
   ```

## Setup

1. Create a `config.py` file:

   ```python
   api_id = "YOUR_API_ID"
   api_hash = "YOUR_API_HASH"
   bot_token = "YOUR_BOT_TOKEN"
   authorization_header = "YOUR_MIDTRANS_AUTHORIZATION_HEADER"
   ```

2. Run the bot:
   ```bash
   python bot.py
   ```

## Usage

1. **Start the bot**: Send the `/start` command to the bot to initialize and display the available options.
2. **Add to Cart**: Click on the product buttons to add items to your cart.
3. **View Cart**: Click on the "View Cart" button to see the items in your cart and proceed to checkout.
4. **Checkout**: Click the "Checkout" button to generate a QRIS code for payment.
5. **Check Status**: Use the "Check Status" button to verify the payment status of your order.
6. **View Pending Orders**: Click the "Check Pending Orders" button to see a list of pending orders.
7. **Send Transactions**: Use the "Send Today's Transactions" button to send a log of today's transactions.

## Code Overview

### `add_transaction()`

Handles adding a new transaction (either debit or credit), updates the total balance, and records the transaction details with a timestamp.

### `show_transactions()`

Displays a list of all recorded transactions with their type, amount, and timestamp.

### `show_total_transactions()`

Shows the current total balance of all transactions.

### `main()`

Provides a menu for interacting with the app, allowing users to add transactions, view transaction history, check total balance, or exit the app.

## Disclaimer

**This project only works in sandbox mode.** It is intended for testing purposes only and should not be used in a production environment. Ensure you have the necessary API keys and authorization headers configured for sandbox use.

## Contributions

Contributions are welcome! Please fork this repository and submit a pull request with your changes.
