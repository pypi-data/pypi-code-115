# -*- coding: utf-8 -*-
from setuptools import setup

package_dir = \
{'': 'src'}

packages = \
['multipage_streamlit']

package_data = \
{'': ['*']}

install_requires = \
['streamlit>=1.7']

setup_kwargs = {
    'name': 'multipage-streamlit',
    'version': '0.1.0',
    'description': 'MultiPage Streamlit app with persistent widget states',
    'long_description': '# MultiPage Streamlit\nMultiPage Streamlit app with persistent widget states\n\n## Demo\nRun the demo app: https://share.streamlit.io/crxi/multipage_streamlit/main/example/demo/app.py\n\n## Background\nRecently I needed an app that supports multiple pages. However, Streamlit does not yet have such a feature.\nNot surprisingly, many innovative developers have came up with their own workarounds. Often it involves using\nthe selectbox as a drop-down menu to offer pages. One such implementation that I like can be found here:\nhttps://towardsdatascience.com/creating-multipage-applications-using-streamlit-efficiently-b58a58134030.\nIt structure each page as a separate module in a package directory, which leads to a nice modular design.\n\nWhile that solution works, **the pages generated do not remember their states when we switch pages**. E.g. if I\nchange a slider from default value of 0 to 10 on Page A and I moved to Page B to do something, then when I\nswitch back to Page A, the slider is again at default 0. I thought saving the values into session_state will\nhelp, but frustratingly it does not. The reason is addressed here: https://github.com/streamlit/streamlit/issues/3925.\nBy design, the values of widgets stored in session_state are removed if they no longer appear on the current page.\n\nThat same ticket implemented a solution to make the values persist. It does it by intercepting "on_change"\nso that it can save the value into a persistent dictionary in session_state. I thought it was pretty clever,\nalthough it does add some complexity if we want to use "on_change".\n\nThen I came across this: https://github.com/streamlit/streamlit/issues/4338. The purposed solution (in the comment)\nhad a different approach which does not involve using "on_change". While it did not work out-of-the-box for me as my\napp spanned different modules, it inspired me to come up with a different solution.\n\n## What\'s new here?\nI combined the solutions and got something that worked for my purpose. And so I would like to\nshare it with the Streamlit Community.\n\nI added some other features:\n- 3 different styles of multipage app: selectbox, expander and radio.\n- allow setting of default value when declaring key name\n- concept of namespace-prefix when saving states to avoid accidental reuse of key names (especially if the\n  pages span multiple modules)\n\n\n## Installation\n```\npython -m pip install git+https://github.com/crxi/multipage_streamlit\n```\n\n## Usage\nOrganize your pages as follows:\n```\n  app.py\n  pages/\n   +- page_a.py\n   +- page_b.py\n```\n\nYour top level app.py:\n```\nimport multipage_streamlit as mt\nfrom pages import page_a, page_b\n\napp = mt.MultiPage()\napp.add("Page A", page_a.run)\napp.add("Page B", page_a.run)\napp.run_selectbox()\n# alternatives: app.run_expander() or app.run_radio() if you prefer those \n```\n\nIn each page.py:\n```\nimport streamlit as st\nfrom multipage_streamlit import State\n\ndef run():\n    state = State(__name__)\n    # the above line is required if you want to save states across page switches.\n    # you can provide your own namespace prefix to make keys unique across pages.\n    # here we use __name__ for convenience.\n    st.header("Page A")\n    \n    x = st.slider("Value X", min_value=0, max_value=100, key=state("x", 50))\n    # here\'s the "magic": state(name, default, ...) returns the namespace-prefixed\n    # key name. if a previously saved state exist, the widget is set to it. if not,\n    # the widget is set to default if it is specified.\n    \n    state.save()  # MUST CALL THE ABOVE TO SAVE THE STATE!\n```\n\nSee the demo for more examples.\n\n## Feedback\nYour feedback is most welcomed. You can send via "Issues" or email to crxi.code@gmail.com.\n\n## Contributing\nInterested in contributing? Check out the contributing guidelines.\nPlease note that this project is released with a Code of Conduct.\nBy contributing to this project, you agree to abide by its terms.\n\n## License\n`multipage_streamlit` was created by CRXi <crxi.code@gmail.com>.\nIt is licensed under the terms of the Apache License 2.0 license.\n\n## Credits\n`multipage_streamlit` was created with [`cookiecutter`](https://cookiecutter.readthedocs.io/en/latest/)\nand the `py-pkgs-cookiecutter` [template](https://github.com/py-pkgs/py-pkgs-cookiecutter).\n',
    'author': 'CRXi',
    'author_email': 'crxi.code@gmail.com',
    'maintainer': None,
    'maintainer_email': None,
    'url': None,
    'package_dir': package_dir,
    'packages': packages,
    'package_data': package_data,
    'install_requires': install_requires,
    'python_requires': '>=3.8,<4.0',
}


setup(**setup_kwargs)
