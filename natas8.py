import base64
encoded_hex = "3d3d516343746d4d6d6c315669563362"

# 1. Hex -> ASCII (hex2bin)
step1 = bytes.fromhex(encoded_hex).decode("ascii")

# 2. 문자열 뒤집기 복원 (strrev의 반대는 다시 strrev)
step2 = step1[::-1]

# 3. Base64 디코딩
secret = base64.b64decode(step2).decode("utf-8")

print("Original Secret:", secret)
