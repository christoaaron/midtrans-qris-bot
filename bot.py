# Import necessary packages
import os
import json
import requests
from datetime import datetime
from pytz import timezone
from telethon import TelegramClient, events
from telethon.tl.custom import Button
import time

# Configuration
api_id = "SET_YOUR_API_ID_HERE"  # Your API ID
api_hash = "SET_YOUR_API_HASH_HERE"  # Your API Hash
bot_token = "SET_YOUR_BOT_TOKEN_HERE"  # Your Bot Token
authorization_header = "SET_YOUR_MIDTRANS_AUTHORIZATION_HEADER_HERE"  # Your Midtrans Authorization Header (Basic Base64 Encoded)

client = TelegramClient('qris_bot', api_id, api_hash).start(bot_token=bot_token)
gmt7 = timezone('Asia/Jakarta')

# Global state
total_transactions = 0
total_gross_amount = 0.0
user_carts = {}
pending_orders = {}
user_messages = {}

# Store products in a list, adjust product details as needed
products = [
    {"id": 1, "name": "Product A", "price": 10000},
    {"id": 2, "name": "Product B", "price": 15000},
    {"id": 3, "name": "Product C", "price": 20000},
    {"id": 4, "name": "Product D", "price": 30000}
]

# Function to generate unique order ID, using current time and date as the order ID in the format "order_YYYYMMDDHHMMSS"
# For example, if the current time is 2023-03-01 12:00:00, the order ID will be "order_20230301120000"
def generate_qris_order_id():
    current_time = datetime.now(gmt7).strftime('%Y%m%d%H%M%S')
    return f'order_{current_time}'

# Function to log successful transactions to a file in the format "order_ID\n"
# For example, if today's date is 2023-03-01, the file name will be "2023-03-01_transactions.txt"
def log_successful_transaction(order_id, cart_items):
    today_date = datetime.now(gmt7).strftime('%Y-%m-%d')
    filename = f'{today_date}_transactions.txt'
    with open(filename, 'a') as file:
        file.write(f'{order_id}\n')
        for item in cart_items:
            file.write(f"{item['name']} - Quantity: {item['quantity']}, Price: {item['price']}\n")

# Function to load total transactions and gross amount from a JSON file
def load_totals():
    global total_transactions, total_gross_amount
    try:
        with open('totals.json', 'r') as file:
            data = json.load(file)
            total_transactions = data.get('total_transactions', 0)
            total_gross_amount = data.get('total_gross_amount', 0.0)
    except (FileNotFoundError, json.JSONDecodeError):
        pass

# Function to save total transactions and gross amount to a JSON file
def save_totals():
    data = {
        'total_transactions': total_transactions,
        'total_gross_amount': total_gross_amount
    }
    with open('totals.json', 'w') as file:
        json.dump(data, file)

# Handle /start command to initialize totals and load buttons and keep track of the dashboard message
@client.on(events.NewMessage(pattern='/start'))
async def handle_start(event):
    load_totals()
    buttons = [[Button.inline(f"{product['name']} - Rp. {product['price']}", f"add_to_cart_{product['id']}")] for product in products]
    buttons.append([Button.inline("View Cart", b"view_cart")])
    buttons.append([Button.inline("Send Today's Transactions", b"send_transactions")])
    buttons.append([Button.inline("Check Pending Orders", b"pending_orders")])
    
    msg = await event.respond(
        f"Welcome to QRIS Bot!\n\n"
        f"Total Transactions: {total_transactions}\n"
        f"Total Gross Amount: Rp. {total_gross_amount}\n\n"
        f"Click a product to add to your cart:",
        buttons=buttons
    )
    # Keep track of the dashboard message
    user_messages[event.sender_id] = [msg.id]

# Handle inline button callback for pending orders (list of pending orders)
@client.on(events.CallbackQuery(data=b'pending_orders'))
async def callback_pending_orders(event):
    if pending_orders:
        pending_orders_list = "\n".join([f"{order['order_id']} - Total Amount: Rp. {order['total_amount']}" for order in pending_orders.values()])
        msg = await event.respond(f"Pending Orders:\n\n{pending_orders_list}\n\n")
        user_messages[event.sender_id].append(msg.id)
    else:
        await event.answer("No pending orders.", alert=True)

# Handle inline button callbacks for adding products to cart (add to cart)
@client.on(events.CallbackQuery(pattern=b'add_to_cart_(\d+)'))
async def callback_add_to_cart(event):
    product_id = int(event.pattern_match.group(1))
    if event.sender_id not in user_carts:
        user_carts[event.sender_id] = []
    existing_item = next((item for item in user_carts[event.sender_id] if item['id'] == product_id), None)
    if existing_item:
        existing_item['quantity'] += 1
        await event.answer("Increased product quantity in cart.")
    else:
        product = next((p for p in products if p['id'] == product_id), None)
        if product:
            user_carts[event.sender_id].append({'id': product_id, 'name': product['name'], 'price': product['price'], 'quantity': 1})
            await event.answer(f"Added {product['name']} to cart.")
        else:
            await event.answer("Product not found.")

# Handle inline button callback for viewing cart (list of items in the cart)
@client.on(events.CallbackQuery(data=b'view_cart'))
async def callback_view_cart(event):
    cart_items = user_carts.get(event.sender_id, [])
    if cart_items:
        cart_details = "\n".join([f"{item['name']} - Rp. {item['price']} (Quantity: {item['quantity']})" for item in cart_items])
        msg = await event.respond(
            f"Your Cart:\n\n{cart_details}\n\n"
            "Click the button below to proceed to checkout:",
            buttons=[[Button.inline("Checkout", b"checkout")]]
        )
        user_messages[event.sender_id].append(msg.id)
    else:
        await event.answer("Your cart is empty.")

# Handle inline button callback for checkout (generate QRIS barcode)
@client.on(events.CallbackQuery(data=b'checkout'))
async def callback_checkout(event):
    cart_items = user_carts.get(event.sender_id, [])
    if not cart_items:
        await event.answer("Your cart is empty.")
        return
    total_amount = sum(item['price'] * item['quantity'] for item in cart_items)
    order_id = generate_qris_order_id()
    url = "https://api.sandbox.midtrans.com/v2/charge"
    payload = {
        "payment_type": "qris",
        "transaction_details": {
            "order_id": order_id,
            "gross_amount": total_amount
        }
    }
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "authorization": authorization_header
    }
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()
        qr_code_url = data['actions'][0]['url']
        pending_orders[event.sender_id] = {'order_id': order_id, 'total_amount': total_amount, 'cart_items': cart_items}
        user_carts.pop(event.sender_id, None)
        msg = await event.respond(
            f"Here is your QR Code for payment:\n{qr_code_url}\n\n"
            "Click the button below to check the payment status:",
            buttons=[
                [Button.inline("Check Status", f"check_status_{order_id}")],
                [Button.inline("Check Pending Orders", b"pending_orders")]
            ]
        )
        user_messages[event.sender_id].append(msg.id)
    except requests.RequestException as e:
        await event.answer(f"Failed to generate QRIS barcode: {str(e)}")

# Handle inline button callback for checking payment status of a pending order (latest order ID)
@client.on(events.CallbackQuery(pattern=b'check_status_(\S+)'))
async def callback_check_status(event):
    order_id = event.pattern_match.group(1).decode('utf-8')
    url = f"https://api.sandbox.midtrans.com/v2/{order_id}/status"
    headers = {
        "accept": "application/json",
        "authorization": authorization_header
    }
    for attempt in range(3):
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            transaction_status = data.get('transaction_status')
            if transaction_status == 'settlement':
                await event.answer("Payment successful!", alert=True)
                total_amount = pending_orders[event.sender_id]['total_amount']
                log_successful_transaction(order_id, pending_orders[event.sender_id]['cart_items'])
                global total_transactions, total_gross_amount
                total_transactions += 1
                total_gross_amount += total_amount
                save_totals()
                pending_orders.pop(event.sender_id, None)
                
                # Delete all user messages except the dashboard
                for msg_id in user_messages.get(event.sender_id, []):
                    try:
                        await client.delete_messages(event.chat_id, msg_id)
                    except Exception as e:
                        print(f"Failed to delete message {msg_id}: {str(e)}")
                
                await client.send_message(event.chat_id, "Payment successful!")
                user_messages[event.sender_id] = [user_messages[event.sender_id][0]]  # Keep only the dashboard message ID
                return
            else:
                await event.answer(f"Payment status: {transaction_status}", alert=True)
                return
        except requests.RequestException as e:
            print(f"Failed to check status (attempt {attempt + 1}): {str(e)}")
        time.sleep(5)
    await event.answer("Failed to retrieve payment status after multiple attempts. Please try again later.", alert=True)

# Handle inline button callback for sending transaction log stored in the folder according to the date of today
@client.on(events.CallbackQuery(data=b'send_transactions'))
async def callback_send_transactions(event):
    today_date = datetime.now(gmt7).strftime('%Y-%m-%d')
    filename = f'{today_date}_transactions.txt'
    if os.path.exists(filename):
        await client.send_file(event.chat_id, filename)
    else:
        await event.answer("No transactions found for today.", alert=True)

# Make sure the bot is running and listening for messages
print("Bot is running...")
client.run_until_disconnected()
