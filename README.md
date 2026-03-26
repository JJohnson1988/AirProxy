# AirProxy
Brokers IPP communication between network printers and Apple devices running modern version of macOS/iOS

Long story short, Apple broke a lot of older printers starting with recent OS versions (like iOS 17). They became a lot more picky about mDNS records and how their devices communicate with network-based printers. So, this fixes that disconnect.

NOTE that you still need some sort of custom mDNS/Avahi record to pair with this script, assuming the record is also incompatible!
