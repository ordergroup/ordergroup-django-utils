module.exports = function (grunt) {
    require('load-grunt-tasks')(grunt);

    grunt.initConfig({
        pkg: grunt.file.readJSON('package.json'),
        coffee: {
            compile: {
                files: {
                    '../og_django_utils/static/og_django_utils/js/progressive-images.js': ['scripts/progressive-images/*.coffee'],
                }
            }
        },
        compass: {
            main: {
                options: {
                    sassDir: 'styles/',
                    cssDir: '../og_django_utils/static/og_django_utils/css',
                    generatedImagesDir: '../src/og_django_utils/static/og_django_utils/css/img',
                    imagesDir: 'images',
                    httpImagesPath: 'img',
                    httpGeneratedImagesPath: 'img',
                    relativeAssets: false
                    //sourcemap: true
                },
                compile: {
                    options: {
                        debugInfo: false,
                        outputStyle: 'compressed'
                    }
                }
            }
        },
        watch: {
            compass: {
                files: ['styles/{,*/}*.{scss,sass}'],
                tasks: ['compass:main:compile']
            },
            coffee: {
                files: ['scripts/{,*/}*.coffee'],
                tasks: ['coffee:compile']
            }
        }
    });

    grunt.loadNpmTasks('grunt-contrib-coffee');
    grunt.loadNpmTasks('grunt-contrib-compass');
    grunt.loadNpmTasks('grunt-contrib-watch');

    grunt.registerTask('build', ['coffee', 'compass']);
};
