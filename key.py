import rsa

p_key, s_key = rsa.newkeys(256, accurate=False)

print(p_key.n)

message = 'banan'
print(message)

message_sign = rsa.sign(message, s_key)


encrypted_message = rsa.encrypt(message.encode(),  p_key)
print(encrypted_message)

decrypted_message = rsa.decrypt(encrypted_message, s_key)
print(decrypted_message.decode())


