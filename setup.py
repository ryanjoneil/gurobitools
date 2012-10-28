from distutils.core import setup

setup (
    name         = 'gurobitools',
    version      = '0.0.1',
    description  = 'Extensions for some advanced IP techniques with gurobipy',
    author       = "Ryan J. O'Neil",
    author_email = 'ryanjoneil@gmail.com',
    url          = 'http://bitbucket.org/ryanjoneil/gurobitools',
    download_url = 'http://bitbucket.org/ryanjoneil/gurobitools/downloads',

    package_dir = {'': 'src'},
    packages    = ['gurobitools'],
    scripts     = ['scripts/gurobitools-lr'],

    keywords    = 'operations research integer programming gurobi',
    classifiers = [
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: BSD License',
        'Topic :: Scientific/Engineering :: Mathematics'
    ]
)
