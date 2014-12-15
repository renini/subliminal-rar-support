subliminal-rar-support
======================

Subliminal - Subtitles (rar-support)

    This python script downloads subtitles for packed (.rar) releases using the subliminal module.
    I like to keep my downloads stored in this 'packed' splitted rar form (.rar, .r00, .r01, r02, etc.).

    The script uses rarfile to get the movie/tvshow filename inside the .rar archives.
    Since we need to calculate filehashes for opensubtitles and subdb this only works on 'store' rars
    these are so called 0x30 (m0) compressed archives.
    Code is ugly, but so far this seems to work for me just fine.
    Hopefully i will find some time to clean the 'code' and release this as a patch for subliminal. Hellup!?

    Enjoy!

