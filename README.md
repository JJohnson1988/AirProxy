# AirProxy
Brokers IPP communication between network printers and Apple devices running modern versions of macOS/iOS

Long story short, Apple broke a lot of older printers starting with recent OS versions (like iOS 17). They became a lot more picky about mDNS records and how their devices communicate with network-based printers. Unfortunately, they never told anyone what they did, and many device manufacturers haven't released updated printer firmware to match new requirements. So, this fixes that disconnect (without any help from Apple).

NOTE that you still need some sort of custom mDNS/Avahi record to pair with this script, assuming your record is also incompatible!
