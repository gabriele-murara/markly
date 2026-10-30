# Installazione di markly su Lubuntu 24.04 (e altre Ubuntu 24.04).
#
#   sudo make deps          pacchetti di sistema necessari (una volta sola)
#   make                    ambiente virtuale, test e bundle in dist/markly/
#   sudo make install       installa in /usr/local
#   make install PREFIX=$HOME/.local  installa solo per l'utente corrente, senza sudo
#   sudo make uninstall     rimuove l'installazione

PREFIX  ?= /usr/local
DESTDIR ?=
APPDIR   = $(PREFIX)/lib/markly
BINDIR   = $(PREFIX)/bin
DATADIR  = $(PREFIX)/share/applications

PYTHON  ?= python3
VENV     = .venv
BUNDLE   = dist/markly/markly
SOURCES  = $(wildcard markly/*.py) markly/style.css .version \
           packaging/markly.spec packaging/launcher.py

# Python 3.12, venv, librerie richieste dal plugin xcb di Qt 6 e binutils per PyInstaller.
APT_PACKAGES = python3 python3-venv python3-pip binutils \
               libxcb-cursor0 libxkbcommon-x11-0 libxcb-icccm4 libxcb-keysyms1 \
               libxcb-shape0 libxcb-xinerama0 libnss3 libasound2t64

.PHONY: all deps venv test bundle install uninstall clean distclean help

all: test bundle

help:
	@sed -n '2,8p' Makefile | sed 's/^# \{0,1\}//'

deps:
	apt-get update
	apt-get install -y $(APT_PACKAGES)

$(VENV)/.stamp: requirements.txt pyproject.toml
	test -x $(VENV)/bin/python || $(PYTHON) -m venv $(VENV)
	$(VENV)/bin/pip install -r requirements.txt
	$(VENV)/bin/pip install -e '.[dev]'
	touch $@

venv: $(VENV)/.stamp

test: $(VENV)/.stamp
	$(VENV)/bin/python -m pytest

$(BUNDLE): $(VENV)/.stamp $(SOURCES)
	$(VENV)/bin/pyinstaller --noconfirm packaging/markly.spec

bundle: $(BUNDLE)

# Non dipende da $(BUNDLE): con sudo la build verrebbe fatta da root.
install:
	@test -x $(BUNDLE) || { echo "Bundle assente: esegui prima 'make'."; exit 1; }
	rm -rf $(DESTDIR)$(APPDIR)
	install -d $(DESTDIR)$(APPDIR) $(DESTDIR)$(BINDIR) $(DESTDIR)$(DATADIR)
	cp -a dist/markly/. $(DESTDIR)$(APPDIR)/
	ln -sf $(APPDIR)/markly $(DESTDIR)$(BINDIR)/markly
	sed 's|^Exec=markly|Exec=$(BINDIR)/markly|' packaging/markly.desktop \
		> $(DESTDIR)$(DATADIR)/markly.desktop
	chmod 644 $(DESTDIR)$(DATADIR)/markly.desktop
	@if [ -z "$(DESTDIR)" ] && command -v update-desktop-database >/dev/null; then \
		update-desktop-database $(DATADIR) || true; fi

uninstall:
	rm -rf $(DESTDIR)$(APPDIR)
	rm -f $(DESTDIR)$(BINDIR)/markly $(DESTDIR)$(DATADIR)/markly.desktop
	@if [ -z "$(DESTDIR)" ] && command -v update-desktop-database >/dev/null; then \
		update-desktop-database $(DATADIR) || true; fi

clean:
	rm -rf build dist

distclean: clean
	rm -rf $(VENV) markly.egg-info .pytest_cache
	find . -name __pycache__ -type d -prune -exec rm -rf {} +
