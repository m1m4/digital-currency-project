from logging.config import listen
from p2pnetwork.node import Node
from fastapi import FastAPI
from multiprocessing import Process
import requests
import api

import uvicorn


app_ = FastAPI()

@app_.get('/')
def home():
    return {'banan': 'ok'}


class FullNode(Node):
    
    
    def __init__(self, host, port=None, id=None, callback=None,
                 max_connections=0):
        
        if port is None:
            port = 13579
              
        super().__init__(host, port, id, callback, max_connections)
        
        self.daemon = True
        
        
    
    def send(self, node, data):
        """Send the data to the node if it exists.
        Same as FullNode.send_to_node(node, data)

        Args:
            node (FullNode): The node to send to
            data (any): the data
        """
        self.send_to_node(node, data) 
    
    def broadcast(self, data, exclude=[]):
        """Send a message to all the nodes that are connected with this node.
        data is a variable which is converted to JSON that is sent over to the
        other node. Same as FullNode.send_to_nodes(data, exclude) 

        Args:
            data (any): the data
            exclude (list): gives all the nodes to which this data should
                            not be sent.
            
        """
        self.send_to_nodes(data, exclude) 
        
    
    # Event functions do not call
    def node_message(self, node, data):
        
        
        data = self.split_data(data)
        
        print(data[0])
        print(data[1])
        
    def split_data(self, data):
        
        decoder = {'t': True, 'f': False, '1': 'block', '2': 'node',
                       '3': 'height', '4': 'hash', '5': 'hxn'}
        
        
        params_decoded = (decoder.get(data[0]), decoder.get(data[1]),
                          decoder.get(data[2]))
        
        
        # return params_decoded, data[3:]
        
        response = requests.get(f'http://127.0.0.1:{10000}')
        
        final = response.content
        print(final)
        return final
            
        
        
    def outbound_node_connected(self, node):
        print("outbound_node_connected: " + node.id)
        
    def inbound_node_connected(self, node):
        print("inbound_node_connected: " + node.id)

    def inbound_node_disconnected(self, node):
        print("inbound_node_disconnected: " + node.id)

    def outbound_node_disconnected(self, node):
        print("outbound_node_disconnected: " + node.id)
        
    def node_disconnect_with_outbound_node(self, node):
        print("node wants to disconnect with oher outbound node: (" + self.id + "): " + node.id)
        
    # def node_request_to_stop(self):
    #     print("Node closing... ")



def connect_to_node(node: FullNode):
    host = input("host or ip of node? ")
    port = int(input("port? "))
    node.connect_with_node(host, port)

if __name__ == "__main__":
    
    # ip = input('Enter ip... ')
    # if not ip:
    #     ip = '127.0.0.1'
        
    # port = int(input('Enter port... '))
    
    
    # node = FullNode(ip, port, id=count)
    # node.start()
    
    
    
    # Implement a console application
    # command = input("? ")
    # while command != "stop" :
        
    #     match command:
    #         case 'connect':
    #             connect_to_node(node)
    #         case 'broadcast':
                
    #             msg = input('Enter message... ')
            
    #             node.broadcast('tf1' + msg)
                
    #         case 'disconnect':
    #             node.disconnect_with_node(node.nodes_outbound[0])
        
    #     # try:
    #     #     eval(command)
        
    #     # except NameError:
    #     #     print('Invalid code')
                     
    #     command = input("? ")
    
    
    
    node1 = FullNode(host='localhost', port=1111, id=1)
    node2 = FullNode(host='localhost', port=2222, id=2)
            
    node1.start()
    node2.start()
    
    node1.connect_with_node('localhost', 2222)
    node1.broadcast('tf1' + 'hello')

    node1.stop()
    node2.stop()
    
    
    