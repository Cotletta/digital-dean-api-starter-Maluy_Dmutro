# Звіт про вимірювання продуктивності криптографічних алгоритмів

- **Система**: Windows (AMD64)
- **Версія Python**: 3.14.3

| Алгоритм | Бекенд | Розмір даних | Запечатування (мс) | Розпечатування (мс) | Пропускна здатність (MB/s) |
|---|---|---|---|---|---|
| AES-128-GCM | cryptography | 64B | 0.00538 | 0.00274 | 7.52 |
| AES-128-GCM | cryptography | 1KB | 0.00287 | 0.00359 | 151.23 |
| AES-128-GCM | cryptography | 64KB | 0.01065 | 0.0095 | 3101.89 |
| AES-128-GCM | cryptography | 1MB | 0.54799 | 0.60209 | 869.51 |
| AES-128-GCM | pycryptodome | 64B | 0.09533 | 0.06291 | 0.39 |
| AES-128-GCM | pycryptodome | 1KB | 0.07188 | 0.06836 | 6.96 |
| AES-128-GCM | pycryptodome | 64KB | 0.1226 | 0.1503 | 229.02 |
| AES-128-GCM | pycryptodome | 1MB | 1.55905 | 1.23076 | 358.45 |
| AES-256-GCM | cryptography | 64B | 0.00299 | 0.00278 | 10.58 |
| AES-256-GCM | cryptography | 1KB | 0.00307 | 0.00296 | 162.18 |
| AES-256-GCM | cryptography | 64KB | 0.01042 | 0.01024 | 3024.79 |
| AES-256-GCM | cryptography | 1MB | 0.57839 | 0.60695 | 843.64 |
| AES-256-GCM | pycryptodome | 64B | 0.05452 | 0.05511 | 0.56 |
| AES-256-GCM | pycryptodome | 1KB | 0.05604 | 0.05659 | 8.67 |
| AES-256-GCM | pycryptodome | 64KB | 0.11479 | 0.11421 | 272.92 |
| AES-256-GCM | pycryptodome | 1MB | 1.1404 | 1.09273 | 447.8 |
| ChaCha20-Poly1305 | cryptography | 64B | 0.00315 | 0.00269 | 10.45 |
| ChaCha20-Poly1305 | cryptography | 1KB | 0.00315 | 0.00312 | 155.88 |
| ChaCha20-Poly1305 | cryptography | 64KB | 0.02113 | 0.02474 | 1362.62 |
| ChaCha20-Poly1305 | cryptography | 1MB | 0.7576 | 0.75045 | 663.11 |
| ChaCha20-Poly1305 | pycryptodome | 64B | 0.02425 | 0.02343 | 1.28 |
| ChaCha20-Poly1305 | pycryptodome | 1KB | 0.02513 | 0.02509 | 19.45 |
| ChaCha20-Poly1305 | pycryptodome | 64KB | 0.12244 | 0.11852 | 259.38 |
| ChaCha20-Poly1305 | pycryptodome | 1MB | 1.71218 | 1.7 | 293.07 |