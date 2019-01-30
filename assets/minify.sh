#npm install -g purifycss uglify-js uglify-es
sass --sourcemap=none style.scss:../static/style.css

purifycss ../static/style.css ../templates/*.html ../static/script.js -min -o ../static/style.css --whitelist is-active
uglifyjs script.js --compress -o ../static/script.js