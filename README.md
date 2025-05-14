# Korepetycje App Frontend (Azure)

Instrukcja deploy’u frontendu na Azure App Service z obrazem z GitHub Container Registry.

Autorzy: Jakub Kucharek, Igor Osiakowski, Mateusz Ługowski, Mikołaj Lewandowski, Michał Kruczyński

### 1. **Repozytorium**  
   https://github.com/ProjBezpieczenstwo/frontend

### 2. **Utwórz App Service**  
   - Typ: Web App for Containers  
   - OS: Linux  
   - Region: Polska (Central Europe)  
   - Kontener:
     - Registry: GitHub Container Registry (`ghcr.io`)
     - Image: `projbezpieczenstwo/frontend:<tag>`

### 3. **Ustaw zmienne środowiskowe** w sekcji Configuration:

| Nazwa        | Opis                                                    |
| ------------ | ------------------------------------------------------- |
| BACKEND\_URL | URL backendu (np. `http://app-server:5000`)             |
| SECRET\_KEY  | Sekret Flask używany przez frontend (sesje użytkownika) |


> Po dodaniu zmiennych kliknij **Save** i **Restart**.

### 4. **Deploy**  
   - W zakładce Deployment Center wybierz GitHub → main branch.

### 5. **Dostęp**  
   - https://\<twoja-app-frontend\>.azurewebsites.net (szablon)
   - (```https://korepetycje-frontend.<region>.azurewebsites.net```) (przypadek wdrożenia, region to np: polandcentral-01)
   - https://\<twoja-app-frontend>.azurewebsites.net/admin/register (rejestracja jako admin)
   - https://\<twoja-app-frontend>.azurewebsites.net/auth/test/register (omijanie SMTP)

