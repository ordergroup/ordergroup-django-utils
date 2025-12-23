((root, factory) ->
    if typeof define == 'function' and define.amd
        define ->
            factory root
    else if typeof exports == 'object'
        module.exports = factory
    else
        root.progressively = factory(root)
    return) this, (root) ->
    extend = (primaryObject, secondaryObject) ->
        o = {}
        for prop of primaryObject
            o[prop] = if secondaryObject.hasOwnProperty(prop) then secondaryObject[prop] else primaryObject[prop]
        o

    ###*
    # Checks, if element is hidden
    # @param  object DOMElement
    # @return {Boolean}    [description]
    ###
    isHidden = (el) ->
        el.offsetParent == null

    ###*
    # Check if element is currently visible
    # @param  object DOMElement
    # @return boolean
    ###
    inView = (el) ->
        if el.classList.contains('progressive--always-load')
            return true

        if isHidden(el)
            return false
        box = el.getBoundingClientRect()
        top = box.top
        height = box.height
        loop
            el = el.parentNode
            unless el != document.body
                break
            box = el.getBoundingClientRect()
            if !(top <= box.bottom)
                return false
            if top + height <= box.top
                return false
        top <= document.documentElement.clientHeight

    removeLoader = (el) ->
        loader = el.classList.contains('img-loader')
        progressBar = el.parentNode.querySelector('.progress-bar')
        if loader
            parent = el.parentNode
            child = parent.querySelector(".svg-spinner")
            child.style.display = 'none'
        if progressBar
            setTimeout (->
              progressBar.classList.add 'hidden'
              return
            ), 450
        return
    updateProgressBar = (el, percentage) ->
      bar = el.parentNode.querySelector('.progress-loader')
      if bar
        bar.style.marginLeft = percentage + "%"
      return

    ###*
    # Load image and add loaded-class. Loads the minified version, if small display
    # @param  object DOMElement
    # @param  object defaults
    # @return boolean true, if fully loaded; false, if minified version was loaded
    ###
    loadImage = (el, defaults) ->
        setTimeout (->
            img = new Image
            xmlHTTP = new XMLHttpRequest()
#            img.src = el.src
            img.onload = ->
                removeLoader(el)
                el.classList.remove 'progressive--not-loaded'
                el.classList.add 'progressive--is-loaded'
                if el.classList.contains('progressive__bg')
                    # Load image as css-background-image
                    el.style['background-image'] = 'url("' + @src + '")'
                else
                    el.src = @src
                onLoad el
                return

            img.onerror = ->
                removeLoader(el)

            # Load minified version, if viewport-width is smaller than defaults.smBreakpoint:
            if getClientWidth() < defaults.smBreakpoint and el.getAttribute('data-progressive-sm')
                el.classList.add 'progressive--loaded-sm'
                img.src = el.getAttribute('data-progressive-sm')
            el.classList.remove 'progressive--loaded-sm'
            imgUrl = el.getAttribute('data-progressive')
            xmlHTTP.open('GET', imgUrl,true)
            imgUrl = el.getAttribute('data-progressive')
            xmlHTTP.open('GET', imgUrl,true);
            xmlHTTP.responseType = 'arraybuffer'
            xmlHTTP.onload = (e) ->
              blob = new Blob([this.response])
              img.src = window.URL.createObjectURL(blob)
            xmlHTTP.onprogress = (e) ->
              completedPercentage = parseInt((e.loaded / e.total) * 100)
              updateProgressBar(el, completedPercentage)
            xmlHTTP.onloadstart = (e) ->
              updateProgressBar(el, 5)
            xmlHTTP.send()
            return
        ), defaults.delay
        return

    ###*
    # Returns the width of the client's viewport
    # @return integer client-width
    ###
    getClientWidth = ->
        Math.max document.documentElement.clientWidth, window.innerWidth or 0

    ###*
    # Listens to an event, and throttles
    ###
    listen = ->
        if poll
            return
        clearTimeout poll
        poll = setTimeout((->
            progressively.check()
            progressively.render()
            poll = null
            return
        ), defaults.throttle)
        return

    progressively = {}
    defaults = undefined
    poll = undefined
    onLoad = undefined
    inodes = undefined
    sminodes = undefined

    onLoad = ->
        ###
        # default settings
        ###

    defaults =
        throttle: 300
        delay: 100
        onLoadComplete: ->
        onLoad: ->
        smBreakpoint: 600

    ###*
    # Initializer. Finds image-elements and adds listeners.
    # @param  object options
    ###
    progressively.init = (options) ->
        options = options or {}
        defaults = extend(defaults, options)
        onLoad = defaults.onLoad or onLoad
        inodes = [].slice.call(document.querySelectorAll('.progressive__img, .progressive__bg'))
        sminodes = []
        progressively.render()
        if document.addEventListener
            root.addEventListener 'scroll', listen, false
            root.addEventListener 'resize', listen, false
            root.addEventListener 'load', listen, false
        else
            root.attachEvent 'onscroll', listen
            root.attachEvent 'onresize', listen
            root.attachEvent 'onload', listen
        return

    ###*
    # Loads necessary images in small or full quality.
    ###
    progressively.render = ->
        elem = undefined
        i = inodes.length - 1
        while i >= 0
            elem = inodes[i]
            if inView(elem) and (elem.classList.contains('progressive--not-loaded') or elem.classList.contains('progressive--loaded-sm'))
                loadImage elem, defaults
                if elem.classList.contains('progressive--loaded-sm')
                    sminodes.push elem
                inodes.splice i, 1
            --i
        if getClientWidth() >= defaults.smBreakpoint
            j = sminodes.length - 1
            while j >= 0
                elem = sminodes[j]
                if inView(elem) and (elem.classList.contains('progressive--not-loaded') or elem.classList.contains('progressive--loaded-sm'))
                    loadImage elem, defaults
                    sminodes.splice i, 1
                --j
        @check()
        return

    ###*
    # Check if all images are loaded in full quality, then drop.
    ###
    progressively.check = ->
        if !inodes.length and !sminodes.length
            defaults.onLoadComplete()
            @drop()
        return

    ###*
    # Drops progressively-listeners
    ###
    progressively.drop = ->
        if document.removeEventListener
            root.removeEventListener 'scroll', listen
            root.removeEventListener 'resize', listen
        else
            root.detachEvent 'onscroll', listen
            root.detachEvent 'onresize', listen
        clearTimeout poll
        return
    progressively

do (window) ->
    # main function to blur images
    window.renderProgressiveImages = (useProgressively=true) ->
        if useProgressively
            progressively.init()
            return

        containers = $('.progressive')
        if containers.length == 0
            console.log('No progressive images found.')
            return

        containers.each ->
            container = $(@)
            fullSrc = container.data('full-src')
            thumbSrc = container.data('src')
            thumbWidth = container.data('thumb-width')
            thumbHeight = container.data('thumb-height')

            # set a bottom padding to avoid glimmer
            if thumbWidth
                @.style.paddingBottom = thumbHeight / thumbWidth * 100 + '%'
            else
                @.style.paddingBottom = thumbHeight + 'px'

            thumb = new Image
            thumb.src = thumbSrc

            thumb.onload = ->
                $(thumb).addClass('thumb-loaded')
                return

            @.appendChild(thumb)
            realImg = new Image
            realImg.src = fullSrc
            realImg.onload = ->
                $(realImg).addClass('large-loaded')
                $(thumb).addClass('thumb-hidden')
                return

            @.appendChild(realImg)
            return
        return
    return
