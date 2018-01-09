from tkinter import *
from tkinter import ttk
from tkinter import messagebox
import socket
import requests
import json


def connect_to_server():
    global address
    global port
    sock = socket.socket()
    # address = e1.get()
    # port = e2.get()

    address = "127.0.0.1"
    port = "5000"

    if address is "" or port is "":
        messagebox.showerror("Error", "Please input correct address and port")
        return
    try:
        sock.connect((address, int(port)))
        messagebox.showinfo("Connected", "Successfully connected")
        sock.close()
        connectWindow.destroy()
        choiceWindow.mainloop()
    except socket.error as e:
        print("Could not connect")
        print(e)
        messagebox.showerror("Error", str(e))


def get_blockchain():
    global parsedResponse
    # response = requests.get("http://" + address + ":" + port + "/chain").content
    chainDetailsTree.delete(*chainDetailsTree.get_children())
    response = requests.get("http://" + "127.0.0.1" + ":" + str(5000) + "/chain").content
    parsedResponse = json.loads(response)
    # parsedBlockchain = json.dumps(parsedResponse, indent=4, sort_keys=True)

    # print(parsedBlockchain)
    for node in parsedResponse['chain']:
        chainDetailsTree.insert('', 'end', text="Block " + str(node['index']), values=(
            node['index'], node['timestamp'], node['nonce'], node['previous_hash'], node['block_hash']))


def show_transactions():
    nodeTransactions = (list(parsedResponse['chain'])[int(chainDetailsTree.focus()[1:], 16) - 1]['transactions'])
    popupWindow = Toplevel(choiceWindow)
    popupTree = ttk.Treeview(popupWindow, columns=('sender', 'recipient', 'amount'))

    popupTree['columns'] = ('sender', 'recipient', 'amount')
    popupTree.heading('sender', text='sender')
    popupTree.heading('recipient', text='recipient')
    popupTree.heading('amount', text='amount')
    popupTree.pack(fill=BOTH, expand=1)
    for transaction in nodeTransactions:
        popupTree.insert('', 0, text="",
                         values=(transaction['sender'], transaction['recipient'], transaction['amount']))


# Connect window
connectWindow = Tk()
connectWindow.title("Client")
Label(connectWindow, text="Address: ").grid(row=0)
Label(connectWindow, text="Port: ").grid(row=1)

e1 = Entry(connectWindow)
e1.grid(row=0, column=1)
e2 = Entry(connectWindow)
e2.grid(row=1, column=1)

connectButton = Button(connectWindow, text="Connect", command=connect_to_server)
connectButton.grid(row=2, columnspan=2)
# End of connect window


# Choice window
choiceWindow = Tk()
choiceWindow.title("MeterejiCoin client")

notebookWidget = ttk.Notebook(choiceWindow)
notebookWidget.pack(expand=1, fill='both')

# Get full chain
fullChainWindow = Frame(choiceWindow)
fullChainWindow.pack(fill='both', expand=1)

getButton = ttk.Button(fullChainWindow, text="Get chain", command=get_blockchain)
getButton.pack(fill='both', expand=1)

chainDetailsTree = ttk.Treeview(fullChainWindow,
                                columns=('index', 'timestamp', 'nonce', 'previous_hash', 'block_hash'))
chainDetailsTree['columns'] = ('index', 'timestamp', 'nonce', 'previous_hash', 'block_hash')
chainDetailsTree.heading('index', text='index')
chainDetailsTree.heading('timestamp', text='timestamp')
chainDetailsTree.heading('nonce', text='nonce')
chainDetailsTree.heading('previous_hash', text='previous_hash')
chainDetailsTree.heading('block_hash', text='block_hash')
chainDetailsTree.pack(fill='both', expand=1)

showTransactionsButton = ttk.Button(fullChainWindow, text="Show transactions", command=show_transactions)
showTransactionsButton.pack(fill='both', expand=1)

# Add tabs to the notebook
notebookWidget.add(fullChainWindow, text="Blockchain")

if __name__ == "__main__":
    connectWindow.mainloop()
