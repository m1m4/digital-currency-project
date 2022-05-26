import tkinter as tk
from tkinter import messagebox
from turtle import tilt

from wallet import Wallet
from threading import Thread
import mnemonic
import websocket
import pyperclip
import json


class App(tk.Tk):
    
    def __init__(self, port=11111) -> None:
        super().__init__()
        
        self.wallet = None
        self.port = port
        
        self.geometry("450x100")
        self.title("Digital Wallet")
        self.main_frm = tk.Frame()
        
        menu = tk.Menu(self)
        config = tk.Menu(menu, tearoff=0)
        config.add_command(label='From mnemonic phrase...', command=self.open_mnemonic_window)
        
        menu.add_cascade(label="Wallet", menu=config)
        menu.add_command(label="Help", command=lambda: HelpWindow(self))
        
        
        self.info_frm = tk.Frame(self)
        self.address_lbl = tk.Label(self.info_frm, text="Address: None")
        self.copy_btn = tk.Button(self.info_frm, text="Copy address", command=lambda: pyperclip.copy(self.address_lbl['text'][9:]))
    
        self.top_frm = tk.Frame(self.main_frm)
        self.bottom_frm = tk.Frame(self.main_frm)
        
        
        self.to_lbl = tk.Label(self.top_frm, text="To:")
        self.amount_lbl = tk.Label(self.top_frm, text="Amount:")
        
        self.to_ent = tk.Entry(self.bottom_frm, width=38)
        self.amount_ent = tk.Entry(self.bottom_frm, width=12)
        self.send_btn = tk.Button(self.bottom_frm, text="Send!", padx=14, command=self.send_btn_click)
        
        self.config(menu=menu)
        
        
    def pack_all(self):
        self.to_lbl.pack(side=tk.LEFT)
        self.amount_lbl.pack(side=tk.LEFT, padx=(220, 0))
        
        self.to_ent.pack(side=tk.LEFT, padx=(0, 5))
        self.amount_ent.pack(side=tk.LEFT, padx=5)
        self.send_btn.pack(side=tk.LEFT, padx=(5, 0))
        
        self.top_frm.pack(side=tk.TOP, anchor="sw")
        self.bottom_frm.pack(side=tk.TOP, padx=20, anchor='s')
        
        self.address_lbl.pack(side=tk.LEFT, padx=(0, 5), anchor="w")
        self.copy_btn.pack(side=tk.LEFT, padx=(5, 0), anchor="w")
        
        self.info_frm.pack(side=tk.TOP, padx=10, pady=5, anchor="w")
        self.main_frm.pack(side=tk.TOP, padx=20, pady=(0, 20))
    
    def run(self):
        
        self.pack_all()
        
        def setup():
            try:
                with open("mnemonic.txt", 'r') as f:
                    words = f.read()
                    if not words:
                        self.grab_set
                        self.open_mnemonic_window()
                        self.grab_release
                    
                    self.wallet = Wallet(words)
                    self.address_lbl.config(text=f"Address: {self.wallet.addr}")
            except FileNotFoundError:
                self.grab_set
                self.open_mnemonic_window()
                self.grab_release
            
        self.wait_visibility()
        setup()
        self.mainloop()
    
    def send_btn_click(self):
        
        amount = self.amount_ent.get()
        address = self.to_ent.get()
        
        if len(self.amount_ent.get()) == 0 or len(self.to_ent.get()) == 0:
            messagebox.showerror(title='Error', message="Please fill the receipient address and amount")
            return
        
        answer = messagebox.askquestion('Confirmation', f'Are you sure you want to send {amount} coins to {address}?')
        
        if answer == 'yes':
            
            if self.wallet is None:
                messagebox.showerror(title='Error', message="Wallet is not set up.")
                return
            
            self.amount_ent.delete(0, 'end')
            self.to_ent.delete(0, 'end')
            
            txn = self.wallet.debug_send(0, (address, int(amount)))
            print('Transaction generated. Sending to node...')
            
            try:
                backend = websocket.create_connection(f"ws://localhost:{self.port}")
                backend.send(json.dumps({'type': 'post', 'data': 
                    {'command': 'post_txn', 'txn': dict(txn._asdict())}}))
                backend.close()
            except ConnectionRefusedError:
                print('Connection refused. Did not send the transaction')

            
    def open_mnemonic_window(self):
        
        mnemonic_window = MnemonicWindow(self)
        
        def get_menmonic():
            words = mnemonic_window.words_txt.get(1.0, "end")
            if not len(mnemonic_window.words_txt.get("1.0", "end-1c")) == 0:
                self.wallet = Wallet(words)
                self.address_lbl.config(text=f"Address: {self.wallet.addr}")
            mnemonic_window.destroy()
          
        mnemonic_window.protocol("WM_DELETE_WINDOW", get_menmonic)
        
 
class MnemonicWindow(tk.Toplevel):
    def __init__(self, master=None) -> None:
        super().__init__(master=master)
        
        self.title("Mnemonic phrase wallet setup")
        self.mnemonic = mnemonic.Mnemonic("English")
        
        self.words_txt = tk.Text(self, width=50, height=6, font= ('Calibri', 12), state="disabled")
        
        self.btn_frame = tk.Frame(self)
        self.load_btn = tk.Button(self.btn_frame, text='Load', command=self.load_btn_click)
        self.generate_btn = tk.Button(self.btn_frame, text='Generate words', command=self.generate_btn_click)
        self.save_btn = tk.Button(self.btn_frame, text='Save', command=self.save_btn_click)
        
        self.pack_all()
        
    
    def pack_all(self):
        
        self.load_btn.pack(side=tk.LEFT, anchor='w', padx=(0, 3))
        self.generate_btn.pack(side=tk.LEFT, anchor='w', padx=(3, 230))
        self.save_btn.pack(side=tk.RIGHT, anchor='e')
        
        self.words_txt.pack(side=tk.TOP, padx=10, pady=(10, 5))
        self.btn_frame.pack(side=tk.TOP, padx=10, pady=(5, 10))
        
    def generate_btn_click(self):
        mnemonic_words = self.mnemonic.generate(strength=256)
        
        self.words_txt.config(state="normal")
        self.words_txt.delete(1.0, "end")
        self.words_txt.insert(1.0, mnemonic_words)
        self.words_txt.config(state="disabled")
        
    def save_btn_click(self):
        
        self.words_txt.config(state="normal")
        words = self.words_txt.get(1.0, "end")
        
        with open('mnemonic.txt', 'w') as f:
            f.write(words)
            
        self.words_txt.config(state="disabled")
        
    def load_btn_click(self):
        
        self.words_txt.config(state="normal")
        self.words_txt.delete(1.0, "end")
        
        try:
            with open("mnemonic.txt", 'r') as f:
                words = f.read()
                self.words_txt.insert(1.0, words)
        except FileNotFoundError:
            messagebox.showerror(title="Error", message="mnemonic.txt does not exist")
            
        self.words_txt.config(state="disabled")
        
    
            
class HelpWindow(tk.Toplevel):
    
    def __init__(self, master=None) -> None:
        super().__init__(master=master)
        
        
        self.master = master
        self.title("Help")
        
        text = '''Welcome to the digital wallet. Here you can
send coins to other nodes in the network. To 
start using the wallet generate your wallet from
a mnemonic phrase and you are ready to go!'''
        
        self.lbl = tk.Label(self, text=text, font= ('Calibri', 17))
        self.pack_all()
        
    def pack_all(self):
        self.lbl.pack(padx=10, pady=10)


def main():
    
    app = App()
    app.run()

if __name__ == "__main__":
    main()
    
