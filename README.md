Given PDFs from Oyster website showing London Bus and Train journeys this script parses the PDFs, extracts line items and outputs a full Pandas DataFrame.

The data is downloaded via:
 * https://oyster.tfl.gov.uk/oyster/showCards.do?method=display
 * "View Joureny History"
 * Select a month to view
 * Download the PDF

Given a PDF file from the Oyster website (or a folder of them), it'll generate an HDF5 based on a DataFrame that looks like:
```
2016-01-27                   Angel          Kentish Town
2016-01-27            Kentish Town                 Angel
2016-01-28            Kentish Town      Leicester Square
2016-01-28        Leicester Square            Old Street
2016-01-28              Old Street          Kentish Town
2016-01-30   Bus Journey, Route 46                      
```

= Examples:

    $ python convert_oyster_pdfs_to_dataframe.py --filename="pdfs/Amex_1001_201511.pdf"  # convert a single PDF

    $ python convert_oyster_pdfs_to_dataframe.py --directory="pdfs"  # search pdfs folder for PDFs


= Tests

```
py.test convert_oyster_pdfs_to_dataframe.py
```
