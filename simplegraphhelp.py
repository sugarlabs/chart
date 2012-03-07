# Help for SimpleGraphActivity

from gettext import gettext as _

from helpbutton import HelpButton


def create_help(toolbar):
    helpitem = HelpButton()
    toolbar.insert(helpitem, -1)
    helpitem.show()
    helpitem.add_section(_('Basic usage'))
    helpitem.add_paragraph(_('First you need add data to create the graph'))
    helpitem.add_paragraph(_('You can add data with this button'),
            'row-insert')
    helpitem.add_paragraph(_('...or remove data with this button'),
            'row-remove')
    helpitem.add_paragraph(_('To change the graph title, just change the activity title'))

    helpitem.add_paragraph(_('Next you can change the type of graph'))
    helpitem.add_paragraph(_('Vertical bars'), 'vbar')
    helpitem.add_paragraph(_('Horizontal bars'), 'hbar')
    helpitem.add_paragraph(_('Lines'), 'line')
    helpitem.add_paragraph(_('Pie'), 'pie')

    helpitem.add_section(_('Configs'))
    helpitem.add_paragraph(_('You can change the colors or the horizontal and vertical labels in the configs toolbar'),
            'preferences-system')

    helpitem.add_section(_('Saving as an image'))
    helpitem.add_paragraph(_('In the activity toolbar you have button to save the graph as an image'),
            'save-as-image')

    helpitem.add_section(_('Reading data from other activities'))
    helpitem.add_paragraph(_('In the activity toolbar you have buttons to read data from other activities'))
    helpitem.add_paragraph(_('You can use times measured in the StopWatch activity'), 'import-stopwatch')
    helpitem.add_paragraph(_('...or data from the Measure activity'), 'import-measure')
