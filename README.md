Given PDFs from Oyster website showing London Bus and Train journeys this script parses the PDFs, extracts line items and outputs a full Pandas DataFrame.

The data is downloaded via:
 1. https://oyster.tfl.gov.uk/oyster/showCards.do?method=display
 1. "View Joureny History"
 1. Select a month to view
 1. Download the PDF

Given a PDF file from the Oyster website (or a folder of them), it'll generate an HDF5 based on a DataFrame that looks like:
```
                             from is_train                 to
date                                                         
2016-01-03           Kentish Town     True   Clapham Junction
2016-01-03       Clapham Junction     True       Kentish Town
2015-12-15               Moorgate     True        Camden Town
2016-01-30  Bus Journey, Route 46    False                   
```

# Examples:

    $ python convert_oyster_pdfs_to_dataframe.py --filename="pdfs/Amex_1001_201511.pdf"  # convert a single PDF

    $ python convert_oyster_pdfs_to_dataframe.py --directory="pdfs"  # search pdfs folder for PDFs


# Tests

```
py.test convert_oyster_pdfs_to_dataframe.py
```
