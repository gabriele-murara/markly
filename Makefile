# Installazione di markly su Lubuntu 24.04 (e altre Ubuntu 24.04).
#
#   sudo make deps          pacchetti di sistema necessari (una volta sola)
#   make                    ambiente virtuale, test e bundle in dist/markly/
#   sudo make install       installa in /usr/local
#   make install PREFIX=$HOME/.local  installa solo per l'utente corrente, senza sudo
#   sudo make uninstall     rimuove l'installazione
#   make deb                pacchetto dist/markly_<versione>_amd64.deb

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

# Per Debian il trattino separa la revisione del pacchetto: 1.0.0-rc1 diventa 1.0.0~rc1.
DEB_VERSION = $(shell sed 's/-/~/g' .version)
DEB_ROOT    = build/deb
DEB         = dist/markly_$(DEB_VERSION)_amd64.deb

# Python 3.12, venv, librerie richieste dal plugin xcb di Qt 6 e binutils per PyInstaller.
APT_PACKAGES = python3 python3-venv python3-pip binutils \
               libxcb-cursor0 libxkbcommon-x11-0 libxcb-icccm4 libxcb-keysyms1 \
               libxcb-shape0 libxcb-xinerama0 libnss3 libasound2t64

.PHONY: all deps venv test bundle deb install uninstall clean distclean help

all: test bundle

help:
	@sed -n '2,9p' Makefile | sed 's/^# \{0,1\}//'

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

$(DEB): $(BUNDLE) packaging/deb/control packaging/markly.desktop LICENSE
	rm -rf $(DEB_ROOT)
	$(MAKE) --no-print-directory install DESTDIR=$(CURDIR)/$(DEB_ROOT) PREFIX=/usr
	install -d $(DEB_ROOT)/DEBIAN $(DEB_ROOT)/usr/share/doc/markly
	install -m 644 LICENSE $(DEB_ROOT)/usr/share/doc/markly/copyright
	sed -e 's/@VERSION@/$(DEB_VERSION)/' \
		-e "s/@SIZE@/$$(du -sk $(DEB_ROOT)/usr | cut -f1)/" \
		packaging/deb/control > $(DEB_ROOT)/DEBIAN/control
	dpkg-deb --root-owner-group -Zxz --build $(DEB_ROOT) $@

deb: $(DEB)

# Non dipende da $(BUNDLE): con sudo la build verrebbe fatta da root.
install:
	@test -x $(BUNDLE) || { echo "Bundle assente: esegui prima 'make'."; exit 1; }
	rm -rf $(DESTDIR)$(APPDIR)
	install -d $(DESTDIR)$(APPDIR) $(DESTDIR)$(BINDIR) $(DESTDIR)$(DATADIR)
	cp -R dist/markly/. $(DESTDIR)$(APPDIR)/
	chmod -R u=rwX,go=rX $(DESTDIR)$(APPDIR)
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
