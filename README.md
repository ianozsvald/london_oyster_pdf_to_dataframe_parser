Given PDFs from Oyster website showing London Bus and Train journeys this script parses the PDFs, extracts line items and outputs a full Pandas DataFrame. Write-up: http://ianozsvald.com/2016/02/07/convert-london-oyster-travel-pdfs-to-pandas-dataframes/

The data is downloaded via:
 1. https://oyster.tfl.gov.uk/oyster/showCards.do?method=display
 1. "View Joureny History"
 1. Select a month to view
 1. Download the PDF

Given a PDF file from the Oyster website (or a folder of them), it'll generate an HDF5 based on a DataFrame that looks like:
```
                             from is_train                to
date                                                        
2016-01-30  Bus Journey, Route 46    False                  
2016-01-28           Kentish Town     True  Leicester Square
2016-01-28             Old Street     True      Kentish Town
2016-01-28       Leicester Square     True        Old Street
2016-01-27                  Angel     True      Kentish Town
```

# Examples:

    $ python convert_oyster_pdfs_to_dataframe.py --filename="pdfs/Amex_1001_201511.pdf"  # convert a single PDF

    $ python convert_oyster_pdfs_to_dataframe.py --directory="pdfs"  # search pdfs folder for PDFs

The data can be loaded back in to Pandas with ```df = pandas.read_hdf('journeys.hdf5')```.

# Tests

```
$ py.test convert_oyster_pdfs_to_dataframe.py
```

# Status

This is a "quick hack" in an evening to process the PDFs, written with:

* Python 3.4
* textract 1.4.0 https://textract.readthedocs.org/en/latest/ (using these Python 3.4 notes: http://www.tysonmaly.com/installing-textract-for-python-3/ )
* pdftotext (Linux) 0.24.5

```
$ pdftotext --help
pdftotext version 0.24.5
Copyright 2005-2013 The Poppler Developers - http://poppler.freedesktop.org
Copyright 1996-2011 Glyph & Cog, LLC
```
