#wygeneruj mi wykres X od Y. X losowe ze zboru 1-100, Y losowe ze zbioru 1-1000
import matplotlib.pyplot as plt
import random
# Generowanie losowych danych
X = [random.randint(1, 100) for _ in range(100)]
Y = [random.randint(1, 1000) for _ in range(100)]

# Tworzenie wykresu punktowego
plt.scatter(X, Y)

# Dodawanie etykiet osi
plt.xlabel('X')
plt.ylabel('Y')

# Dodawanie tytułu wykresu
plt.title('Wykres X od Y')

# Wyświetlanie wykresu
plt.show()