.. _link_shorteners:

***************
Link Shorteners
***************

Lists of known link shorteners recognized by ``pewtils.http`` utility methods such \
as :py:func:`pewtils.http.canonical_link` and :py:func:`pewtils.http.extract_domain_from_url`. These lists were \
compiled from several collections of shortened links found in social media posts and news articles, so most of the \
shorteners belong to news outlets and large popular websites, especially those with political content. Since domains \
can be retired or may change ownership and get redirected to different websites over time, these lists may not \
be perfectly accurate. We will try to keep them updated as we become aware of changes, but if you notice any \
inaccuracies or wish to add to these lists, please consider making a pull request!

.. _gen_link_shorteners:
.. csv-table:: Generic Link Shorteners
   :file: ../pewtils/general_link_shorteners.csv
   :widths: 30
   :header-rows: 1

.. _vanity_link_shorteners:
.. csv-table:: Vanity Link Shorteners
   :file: ../pewtils/vanity_link_shorteners.csv
   :widths: 30, 30, 30
   :header-rows: 1
