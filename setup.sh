#!/bin/bash

# We attempt to determine the path to the higu directory automatically. For
# safety or for alternate installation configurations, you may hardcode the
# path here.
HIGUHOME="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd $HIGUHOME

JQUERY_VER=1.10.2
JQUERY_UI_VER=1.10.3
JQUERY_UI_THEME=smoothness
REACT_VER=15.6.2
BABEL_CORE_VER=5.2.17

rm -rf $HIGUHOME/static/libs
mkdir -p $HIGUHOME/static/libs
cd $HIGUHOME/static/libs

echo 'Downloading and installing jQuery'
echo '============================================================'
wget "http://code.jquery.com/jquery-${JQUERY_VER}.js" -O jquery.js
wget "http://code.jquery.com/ui/${JQUERY_UI_VER}/jquery-ui.js" -O jquery-ui.js
wget "https://jqueryui.com/resources/download/jquery-ui-themes-${JQUERY_UI_VER}.zip"
unzip "jquery-ui-themes-${JQUERY_UI_VER}.zip"
mv "jquery-ui-themes-${JQUERY_UI_VER}/themes/${JQUERY_UI_THEME}/jquery-ui.css" .
mv "jquery-ui-themes-${JQUERY_UI_VER}/themes/${JQUERY_UI_THEME}/images" .
rm -rf "jquery-ui-themes-${JQUERY_UI_VER}.zip" "jquery-ui-themes-${JQUERY_UI_VER}"

echo 'Downloading and installing React'
echo '============================================================'
wget "https://unpkg.com/react@${REACT_VER}/dist/react.js" -O react.js
wget "https://unpkg.com/react-dom@${REACT_VER}/dist/react-dom.js" -O react-dom.js
wget "https://unpkg.com/babel-core@${BABEL_CORE_VER}/browser.js" -O browser.js
