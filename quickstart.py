from pydrive.auth import GoogleAuth

gauth = GoogleAuth()
gauth.LocalWebserverAuth() # Creates local webserver and auto handles authentication.

gauth.SaveCredentialsFile(credentials_file="saved_credentials.json")
