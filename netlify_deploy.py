#!/usr/bin/env python3
"""
Netlify Deploy — Sube reportes HTML a Netlify automáticamente.

Flujo:
1. Primera vez: crea un sitio en Netlify + sube el HTML
2. Siguientes veces: agrega archivos al sitio existente (sin borrar los anteriores)

Configuración necesaria en config.json:
  "netlify_token": "tu_token_de_netlify"
  "netlify_site_id": ""   ← se llena automáticamente la primera vez
"""

import hashlib
import json
import os
import urllib.request
import urllib.error
from pathlib import Path


class NetlifyDeployer:
    """Maneja deploys a Netlify vía API."""

    API_BASE = "https://api.netlify.com/api/v1"

    def __init__(self, token, site_id=None):
        self.token = token
        self.site_id = site_id

    def _request(self, method, path, data=None, content_type="application/json"):
        """Make an API request to Netlify."""
        url = f"{self.API_BASE}{path}"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": content_type,
        }

        if data and content_type == "application/json":
            body = json.dumps(data).encode("utf-8")
        elif data:
            body = data
        else:
            body = None

        req = urllib.request.Request(url, data=body, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8") if e.fp else ""
            raise Exception(f"Netlify API error {e.code}: {error_body}")

    def _file_sha1(self, filepath):
        """Compute SHA1 hash of a file."""
        sha1 = hashlib.sha1()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha1.update(chunk)
        return sha1.hexdigest()

    def create_site(self, name=None):
        """Create a new Netlify site."""
        data = {}
        if name:
            data["name"] = name  # subdomain: name.netlify.app

        result = self._request("POST", "/sites", data)
        self.site_id = result["id"]
        return {
            "site_id": result["id"],
            "url": result["ssl_url"] or result["url"],
            "name": result.get("name", ""),
        }

    def get_existing_files(self):
        """Get list of files currently deployed on the site."""
        if not self.site_id:
            return {}

        try:
            # Get latest deploy
            deploys = self._request("GET", f"/sites/{self.site_id}/deploys")
            if not deploys:
                return {}

            latest = deploys[0]
            deploy_id = latest["id"]

            # Get files in that deploy
            files = self._request("GET", f"/deploys/{deploy_id}/files")
            return {f["path"]: f["sha"] for f in files}
        except:
            return {}

    def deploy(self, files_dict, progress_callback=None):
        """
        Deploy files to the site. Preserves existing files.

        Args:
            files_dict: {"/path/on/site.html": "/local/path/to/file.html"}
            progress_callback: optional function(percent)

        Returns:
            dict with deploy_url and file_urls
        """
        if not self.site_id:
            raise Exception("No site_id configured. Create a site first.")

        # Get existing files to preserve them
        existing_files = self.get_existing_files()
        if progress_callback:
            progress_callback(20)

        # Compute hashes for new files
        file_hashes = {}
        for site_path, local_path in files_dict.items():
            sha1 = self._file_sha1(local_path)
            file_hashes[site_path] = sha1

        # Merge: keep existing + add new (overwrite if same path)
        all_hashes = {**existing_files, **file_hashes}

        if progress_callback:
            progress_callback(40)

        # Create deploy with all file hashes
        deploy_data = {
            "files": all_hashes
        }
        deploy_result = self._request(
            "POST",
            f"/sites/{self.site_id}/deploys",
            deploy_data
        )

        deploy_id = deploy_result["id"]
        required_files = deploy_result.get("required", [])

        if progress_callback:
            progress_callback(60)

        # Upload only the required (new/changed) files
        for site_path, local_path in files_dict.items():
            sha1 = file_hashes[site_path]
            if sha1 in required_files:
                with open(local_path, "rb") as f:
                    file_data = f.read()
                self._request(
                    "PUT",
                    f"/deploys/{deploy_id}/files{site_path}",
                    data=file_data,
                    content_type="application/octet-stream"
                )

        if progress_callback:
            progress_callback(90)

        # Get the final URL
        site_url = deploy_result.get("ssl_url") or deploy_result.get("url", "")

        file_urls = {}
        for site_path in files_dict:
            file_urls[site_path] = f"{site_url}{site_path}"

        if progress_callback:
            progress_callback(100)

        return {
            "deploy_url": site_url,
            "deploy_id": deploy_id,
            "file_urls": file_urls
        }


def setup_netlify(config_path):
    """
    Interactive setup for Netlify. Run once to configure.
    Saves netlify_token and netlify_site_id to config.json.
    """
    print("\n" + "=" * 50)
    print("  Configuración de Netlify")
    print("=" * 50)
    print()
    print("Para subir reportes automáticamente necesitas:")
    print()
    print("  1. Crear una cuenta en netlify.com (gratis)")
    print("  2. Ir a: app.netlify.com/user/applications#personal-access-tokens")
    print("  3. Crear un 'Personal access token'")
    print("  4. Copiar el token y pegarlo aquí")
    print()

    token = input("Pega tu token de Netlify: ").strip()
    if not token:
        print("Token vacío. Cancelando.")
        return

    # Test token
    deployer = NetlifyDeployer(token)
    try:
        deployer._request("GET", "/user")
        print("✅ Token válido!")
    except Exception as e:
        print(f"❌ Token inválido: {e}")
        return

    # Create site
    site_name = input("Nombre del sitio (ej: doit-reportes): ").strip()
    if not site_name:
        site_name = "doit-reportes"

    try:
        site_info = deployer.create_site(site_name)
        print(f"✅ Sitio creado: {site_info['url']}")
    except Exception as e:
        # Site name might be taken, try without custom name
        print(f"Nombre '{site_name}' no disponible, creando con nombre automático...")
        try:
            site_info = deployer.create_site()
            print(f"✅ Sitio creado: {site_info['url']}")
        except Exception as e2:
            print(f"❌ Error creando sitio: {e2}")
            return

    # Save to config
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    config["netlify_token"] = token
    config["netlify_site_id"] = site_info["site_id"]
    config["netlify_url"] = site_info["url"]

    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Configuración guardada en {config_path}")
    print(f"   URL base: {site_info['url']}")
    print()


if __name__ == "__main__":
    config_path = Path(__file__).parent / "config.json"
    setup_netlify(str(config_path))
