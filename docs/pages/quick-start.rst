Quick Start
===========

So you maybe saw our ``README`` with overview of our library. Let's now renew (TODO поновимо інформацію, згадаємо) it and deep in it's details.

What is lookup?
---------------

The first, what we do with the address - lookup it. We need :meth:`~JavaServer.lookup` method for resolving `SRV record <TODO what is SRV record, guide by cloudflare?>`_ and other DNS records (like `CNAME <TODO link to "what is cname">`_).
In short, Minecraft uses SRV record to resolve domain without a port into IP with port. The method, also tries adds standart port, if you provided an IP. (TODO what it does with invalid domains?)

BUT, this was all about Java Edition servers, Bedrock ones don't have any SRV records, and :meth:`~BedrockServer.lookup` just adds standart port (19132), if it wasn't provided.

If you have just IP - ``lookup`` is ridicularios (TODO лишній), it will slow down your status fetching with invalid DNS request (target of request will be the IP). You can call just :class:`JavaServer` (or :class:`BedrockServer`) with the IP and port.

.. code-block:: python

    >>> java_server = JavaServer("123.123.123.123")
    >>> # port authomatically will be mapped to 25565
    >>> java_server.address.port
    25565
    >>> # the same with bedrock servers
    >>> bedrock_server = BedrockServer("123.123.123.123")
    >>> bedrock_server.address.port
    19132
    
This will skip all network operations, and much faster than lookup.

How to get the status?
----------------------


