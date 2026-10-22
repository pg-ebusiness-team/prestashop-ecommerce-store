# Opis architektury kontenerów

Stan architektury będzie rozwijany w czasie, a ninijeszy plik aktualizowany.

## Dockerfile

Na razie **Dockerfile** zawiera jedną linijkę, która bazuje na obrazie kontenera Prestashop w wersji zgodnej z wymaganiami. W przyszłości osoba, która doda pierwszy moduł do sklepu, będzie musiała dopisać linijkę (bądź kilka) z *COPY*. Podobno bazowy template Prestashop aktualizuje się poprzez kopiowane do kontenera moduły, ale trzeba jeszcze zrobić research.

## Plik compose.yaml

Póki co plik zawiera kontener sklepu oraz bazy danych, która bazuje na wolumenie.

### Kontener shop

Zbudowanie kontenera z obrazu w katalogu **../shop**, a następnie nazwanie go:

```yaml
build: ../shop
image: shop:dev
```

Wymuszenie platformy w celu spełnienia narzuconych wymagań:

```yaml
platform: linux/amd64
```

Zmienne środowiskowe:
- DB_SERVER - miejsce istancji mysql
- DB_NAME - nazwa bazy danych
- DB_USER - nazwa użytkownika w bazie danych
- DB_PASSWD - hasło użytkownika w bazie danych
- PS_INSTALL_AUTO - flaga inicjalizująca automatyczną instalację prestashop po uruchomieniu kontenera
- PS_LANGUAGE - bazowy język w Prestashop
- PS_COUNTRY -  bazowy kraj w Prestashop
- PS_DOMAIN - adres sklepu
- ADMIN_MAIL - mail użytkownika admin, używany w panelu admina
- ADMIN_PASSWD - hasło użytkownika admin
- PS_FOLDER_ADMIN - miejsce panelu admina. Adres: PS_DOMAIN/PS_FOLDER_ADMIN

Mapowanie portu dla kontenera:

```yaml
ports:
  - "${SHOP_PORT}:80"
```

### Kontener db

Obraz kontenera oraz wymagana platforma:

```yaml
image: mysql:8.0
platform: linux/amd64
```

Flagi konfiguracyjne potrzebne, aby baza przechowywała polskie znaki

```yaml
command:
  - --character-set-server=utf8mb4
  - --collation-server=utf8mb4_unicode_ci
```

Zmienne środowiskowe:
- MYSQL_ROOT_PASSWORD - hasło użytkownika *root*
- MYSQL_DATABASE - nazwa bazy danych w instancji
- MYSQL_USER - użytkownik mający dostęp tylko do tej bazy danych
- MYSQL_PASSWORD - hasło powyższego użytkownika

Do jakiego katalogu w kontenerze będzie montowany wolumen:

```yaml
volumes:
  - db_data:/var/lib/mysql
```