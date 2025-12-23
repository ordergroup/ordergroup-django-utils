(function() {
  (function(root, factory) {
    if (typeof define === 'function' && define.amd) {
      define(function() {
        return factory(root);
      });
    } else if (typeof exports === 'object') {
      module.exports = factory;
    } else {
      root.progressively = factory(root);
    }
  })(this, function(root) {
    var defaults, extend, getClientWidth, inView, inodes, isHidden, listen, loadImage, onLoad, poll, progressively, removeLoader, sminodes;
    extend = function(primaryObject, secondaryObject) {
      var o, prop;
      o = {};
      for (prop in primaryObject) {
        o[prop] = secondaryObject.hasOwnProperty(prop) ? secondaryObject[prop] : primaryObject[prop];
      }
      return o;
    };

    /**
     * Checks, if element is hidden
     * @param  object DOMElement
     * @return {Boolean}    [description]
     */
    isHidden = function(el) {
      return el.offsetParent === null;
    };

    /**
     * Check if element is currently visible
     * @param  object DOMElement
     * @return boolean
     */
    inView = function(el) {
      var box, height, top;
      if (el.classList.contains('progressive--always-load')) {
        return true;
      }
      if (isHidden(el)) {
        return false;
      }
      box = el.getBoundingClientRect();
      top = box.top;
      height = box.height;
      while (true) {
        el = el.parentNode;
        if (el === document.body) {
          break;
        }
        box = el.getBoundingClientRect();
        if (!(top <= box.bottom)) {
          return false;
        }
        if (top + height <= box.top) {
          return false;
        }
      }
      return top <= document.documentElement.clientHeight;
    };
    removeLoader = function(el) {
      var child, loader, parent, progressBar;
      loader = el.classList.contains('img-loader');
      progressBar = el.parentNode.querySelector('.progress-bar');
      if (loader) {
        parent = el.parentNode;
        child = parent.querySelector(".svg-spinner");
        setTimeout()
        child.style.display = 'none';
      }
      if (progressBar) {
        setTimeout(function(){
          progressBar.classList.add('hidden')
        }, 450);
      }
    };

    updateProgressBar = function(el, percentage) {
      var bar;
      bar = el.parentNode.querySelector('.progress-loader');
      if (bar) {
        bar.style.marginLeft = percentage + "%";
      }
    };

    /**
     * Load image and add loaded-class. Loads the minified version, if small display
     * @param  object DOMElement
     * @param  object defaults
     * @return boolean true, if fully loaded; false, if minified version was loaded
     */
    loadImage = function(el, defaults) {
      setTimeout((function() {
        var img;
        img = new Image;
        var xmlHTTP;
        xmlHTTP = new XMLHttpRequest();
        img.onload = function() {
          removeLoader(el);
          el.classList.remove('progressive--not-loaded');
          el.classList.add('progressive--is-loaded');
          if (el.classList.contains('progressive__bg')) {
            el.style['background-image'] = 'url("' + this.src + '")';
          } else {
            el.src = this.src;
          }
          onLoad(el);
        };
        img.onerror = function() {
          return removeLoader(el);
        };
        if (getClientWidth() < defaults.smBreakpoint && el.getAttribute('data-progressive-sm')) {
          el.classList.add('progressive--loaded-sm');
          img.src = el.getAttribute('data-progressive-sm');
        }
        el.classList.remove('progressive--loaded-sm');
        var imgUrl;
        imgUrl = el.getAttribute('data-progressive');
        xmlHTTP.open('GET', imgUrl,true);
        xmlHTTP.responseType = 'arraybuffer';
        xmlHTTP.onload = function(e) {
            var blob = new Blob([this.response]);
            img.src = window.URL.createObjectURL(blob);
        };
        xmlHTTP.onprogress = function(e) {
            completedPercentage = parseInt((e.loaded / e.total) * 100);
            updateProgressBar(el, completedPercentage);
        };
        xmlHTTP.onloadstart = function() {
            updateProgressBar(el, 5);
        };
        xmlHTTP.send();
      }), defaults.delay);
    };

    /**
     * Returns the width of the client's viewport
     * @return integer client-width
     */
    getClientWidth = function() {
      return Math.max(document.documentElement.clientWidth, window.innerWidth || 0);
    };

    /**
     * Listens to an event, and throttles
     */
    listen = function() {
      var poll;
      if (poll) {
        return;
      }
      clearTimeout(poll);
      poll = setTimeout((function() {
        progressively.check();
        progressively.render();
        poll = null;
      }), defaults.throttle);
    };
    progressively = {};
    defaults = void 0;
    poll = void 0;
    onLoad = void 0;
    inodes = void 0;
    sminodes = void 0;
    onLoad = function() {

      /*
       * default settings
       */
    };
    defaults = {
      throttle: 300,
      delay: 100,
      onLoadComplete: function() {},
      onLoad: function() {},
      smBreakpoint: 600
    };

    /**
     * Initializer. Finds image-elements and adds listeners.
     * @param  object options
     */
    progressively.init = function(options) {
      options = options || {};
      defaults = extend(defaults, options);
      onLoad = defaults.onLoad || onLoad;
      inodes = [].slice.call(document.querySelectorAll('.progressive__img, .progressive__bg'));
      sminodes = [];
      progressively.render();
      if (document.addEventListener) {
        root.addEventListener('scroll', listen, false);
        root.addEventListener('resize', listen, false);
        root.addEventListener('load', listen, false);
      } else {
        root.attachEvent('onscroll', listen);
        root.attachEvent('onresize', listen);
        root.attachEvent('onload', listen);
      }
    };

    /**
     * Loads necessary images in small or full quality.
     */
    progressively.render = function() {
      var elem, i, j;
      elem = void 0;
      i = inodes.length - 1;
      while (i >= 0) {
        elem = inodes[i];
        if (inView(elem) && (elem.classList.contains('progressive--not-loaded') || elem.classList.contains('progressive--loaded-sm'))) {
          loadImage(elem, defaults);
          if (elem.classList.contains('progressive--loaded-sm')) {
            sminodes.push(elem);
          }
          inodes.splice(i, 1);
        }
        --i;
      }
      if (getClientWidth() >= defaults.smBreakpoint) {
        j = sminodes.length - 1;
        while (j >= 0) {
          elem = sminodes[j];
          if (inView(elem) && (elem.classList.contains('progressive--not-loaded') || elem.classList.contains('progressive--loaded-sm'))) {
            loadImage(elem, defaults);
            sminodes.splice(i, 1);
          }
          --j;
        }
      }
      this.check();
    };

    /**
     * Check if all images are loaded in full quality, then drop.
     */
    progressively.check = function() {
      if (!inodes.length && !sminodes.length) {
        defaults.onLoadComplete();
        this.drop();
      }
    };

    /**
     * Drops progressively-listeners
     */
    progressively.drop = function() {
      if (document.removeEventListener) {
        root.removeEventListener('scroll', listen);
        root.removeEventListener('resize', listen);
      } else {
        root.detachEvent('onscroll', listen);
        root.detachEvent('onresize', listen);
      }
      clearTimeout(poll);
    };
    return progressively;
  });

  (function(window) {
    window.renderProgressiveImages = function(useProgressively) {
      var containers;
      if (useProgressively == null) {
        useProgressively = true;
      }
      if (useProgressively) {
        progressively.init();
        return;
      }
      containers = $('.progressive');
      if (containers.length === 0) {
        console.log('No progressive images found.');
        return;
      }
      containers.each(function() {
        var container, fullSrc, realImg, thumb, thumbHeight, thumbSrc, thumbWidth;
        container = $(this);
        fullSrc = container.data('full-src');
        thumbSrc = container.data('src');
        thumbWidth = container.data('thumb-width');
        thumbHeight = container.data('thumb-height');
        if (thumbWidth) {
          this.style.paddingBottom = thumbHeight / thumbWidth * 100 + '%';
        } else {
          this.style.paddingBottom = thumbHeight + 'px';
        }
        thumb = new Image;
        thumb.src = thumbSrc;
        thumb.onload = function() {
          $(thumb).addClass('thumb-loaded');
        };
        this.appendChild(thumb);
        realImg = new Image;
        realImg.src = fullSrc;
        realImg.onload = function() {
          $(realImg).addClass('large-loaded');
          $(thumb).addClass('thumb-hidden');
        };
        this.appendChild(realImg);
      });
    };
  })(window);

}).call(this);