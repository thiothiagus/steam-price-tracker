import logging
import os
import shutil
import time
from pathlib import Path
from threading import Event, Thread

logger = logging.getLogger(__name__)


class SaveWatcher:
    def __init__(
        self,
        source_path: str | Path,
        dest_path: str | Path,
        cooldown_seconds: float = 5.0,
        poll_interval: float = 10.0,
    ) -> None:
        self._source = Path(source_path)
        self._dest = Path(dest_path)
        self._cooldown = cooldown_seconds
        self._poll_interval = poll_interval
        self._stop_event = Event()
        self._thread: Thread | None = None
        self._last_mtime: float = 0.0
        self._last_size: int = 0
        self._error: str | None = None
        self._last_tradable: set[tuple[int, str]] = set()

    @property
    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    @property
    def source_path(self) -> Path:
        return self._source

    @property
    def dest_path(self) -> Path:
        return self._dest

    @property
    def error(self) -> str | None:
        return self._error

    @property
    def source_exists(self) -> bool:
        return self._source.exists()

    def start(self) -> None:
        if self.is_running:
            logger.info("SaveWatcher já está rodando.")
            return
        self._stop_event.clear()
        self._last_mtime = 0.0
        self._last_size = 0
        self._error = None
        self._thread = Thread(target=self._poll_loop, daemon=True, name="save-watcher")
        self._thread.start()
        logger.info(
            "SaveWatcher iniciado: monitorando %s -> %s (cooldown=%ss, poll=%ss)",
            self._source, self._dest, self._cooldown, self._poll_interval,
        )

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("SaveWatcher parado.")

    def _poll_loop(self) -> None:
        while not self._stop_event.is_set():
            try:
                if not self._source.exists():
                    self._error = f"Arquivo não encontrado: {self._source}"
                    logger.warning(self._error)
                    self._stop_event.wait(self._poll_interval)
                    continue

                current_mtime = os.path.getmtime(self._source)
                current_size = os.path.getsize(self._source)

                if current_mtime != self._last_mtime or current_size != self._last_size:
                    self._last_mtime = current_mtime
                    self._last_size = current_size
                    logger.info("Save file modificado. Aguardando cooldown de %ss...", self._cooldown)
                    self._stop_event.wait(self._cooldown)
                    if self._stop_event.is_set():
                        break
                    self._copy_save()

                self._error = None
            except PermissionError:
                logger.debug("Arquivo com lock (permissão negada), tentando novamente...")
                self._error = "Arquivo com lock pelo jogo"
            except OSError as e:
                self._error = str(e)
                logger.warning("Erro ao acessar save file: %s", e)
            except Exception:
                self._error = "Erro inesperado"
                logger.exception("Erro no save watcher")

            self._stop_event.wait(self._poll_interval)

    def _copy_save(self) -> None:
        try:
            old_size = self._dest.stat().st_size if self._dest.exists() else 0
            self._dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(self._source, self._dest)
            new_size = self._dest.stat().st_size
            delta = new_size - old_size
            logger.info(
                "Save copiado: %d bytes (%s%+d bytes) — %s",
                new_size,
                "+" if delta >= 0 else "",
                delta,
                self._dest.name,
            )
            self._log_save_summary()
            self._error = None
        except PermissionError:
            self._error = "Arquivo ainda com lock pelo jogo"
            logger.warning("Arquivo ainda com lock, tentando novamente no próximo ciclo.")
        except Exception:
            self._error = "Falha ao copiar save"
            logger.exception("Falha ao copiar save file")

    def _log_save_summary(self) -> None:
        try:
            from app.utils.save_parser import SaveParser
            parser = SaveParser(self._dest)
            items = parser.get_item_save_datas()
            tradable = parser.get_tradable_items()
            heroes = parser.get_hero_save_datas()

            current_tradable = {(t["item_key"], t["name"]) for t in tradable}
            added = current_tradable - self._last_tradable
            removed = self._last_tradable - current_tradable
            self._last_tradable = current_tradable

            logger.info(
                "Save: %d heróis, %d itens, %d negociáveis",
                len(heroes), len(items), len(tradable),
            )
            for key, name in sorted(added):
                logger.info("  [+] Item negociável adicionado: %s (key=%s)", name, key)
            for key, name in sorted(removed):
                logger.info("  [-] Item negociável removido: %s (key=%s)", name, key)

            from app.services.import_service import import_from_save
            result = import_from_save(self._dest)
            if result["imported"] or result["updated"]:
                logger.info(
                    "Auto-import: %d novos, %d qtds atualizadas",
                    result["imported"], result["updated"],
                )
            if result["imported"]:
                import asyncio
                from app.services.collector_service import collect_all_prices
                asyncio.create_task(collect_all_prices(force=False))
        except Exception:
            logger.debug("Não foi possível extrair resumo do save.")
