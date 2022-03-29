"""
A Grid theme for Altair.
"""
# Color schemes and defaults
palette = dict(
    black="#333333",
    white="#ffffff",
    default="#00d4d8",
    accent="#006d8f",
    highlight="#ec8431",
    democrat="#5789b8",
    republican="#d94f54",
    schemes={
        "category-5": [
            "#005f66",
            "#e37e2d",
            "#d64a3b",
            "#76b0ef",
            "#c1bc40",
        ],
        "teal-6": [
            "#7ff6f6",
            "#00eeef",
            "#00d4d8",
            "#00abb2",
            "#00848b",
            "#fbf2c7",
        ],
        "fireandice-6": [
            "#e68a4f",
            "#f4bb6a",
            "#f9e39c",
            "#dadfe2",
            "#a6b7c6",
            "#849eae",
        ],
        "ice-7": [
            "#edefee",
            "#dadfe2",
            "#c4ccd2",
            "#a6b7c6",
            "#849eae",
            "#607785",
            "#47525d",
        ],
        "cb-diverging-purpgrn": [
            "#762a83",
            "#af8dc3",
            "#e7d4e8",
            "#f7f7f7",
            "#d9f0d3",
            "#7fbf7b",
            "#1b7837",
        ],
    },
)


def theme():
    """
    A Grid theme for Altair.
    """
    # Headlines
    headlineFontSize = 18
    headlineFontWeight = "normal"
    headlineFont = "Summit Sans"

    # Titles for axes and legends
    titleFont = "Roboto"
    titleFontWeight = "normal"
    titleFontSize = 15
    titleFontColor = '#767676'

    # Labels for ticks and legend entries
    labelFont = "Roboto, sans"
    labelFontSize = 13
    labelFontWeight = "normal"
    labelFontColor = '#1a1a1a'
    titleFontColor = '#767676'

    return dict(
        config=dict(
            view=dict(width=650, height=400, strokeOpacity=0),
            background=palette["white"],
            title=dict(
                anchor="start",
                font=headlineFont,
                fontColor='palette["black"]',
                fontSize=headlineFontSize,
                fontWeight=headlineFontWeight,
            ),
            arc=dict(fill=palette["default"]),
            area=dict(fill=palette["default"]),
            line=dict(stroke=palette["default"], strokeWidth=3),
            path=dict(stroke=palette["default"]),
            rect=dict(fill=palette["default"]),
            shape=dict(stroke=palette["default"]),
            bar=dict(fill=palette["default"]),
            point=dict(stroke=palette["default"]),
            symbol=dict(fill=palette["default"], size=30),
            axis=dict(
                titleFont=titleFont,
                titleFontSize=titleFontSize,
                titleFontWeight=titleFontWeight,
                labelFont=labelFont,
                labelFontSize=labelFontSize,
                labelFontWeight=labelFontWeight,
            ),
            axisX=dict(labelAngle=0, labelPadding=6, tickSize=3, grid=False),
            axisY=dict(
                labelBaseline="middle",
                maxExtent=45,
                minExtent=45,
                titleAlign="left",
                titleAngle=0,
                titleX=-60,
                titleY=18,
                domainOpacity=0,
                gridWidth=0.6,
                gridColor="#dddddd",
                offset=6,
                tickSize=0,
                titleColor='#767676'
            ),
            legend=dict(
                titleFont=titleFont,
                titleFontSize=titleFontSize,
                titleFontWeight=titleFontWeight,
                symbolType="square",
                labelFont=labelFont,
                labelFontSize=labelFontSize,
            ),
            range=dict(
                category=palette["schemes"]["category-5"],
                diverging=palette["schemes"]["fireandice-6"],
                heatmap=palette["schemes"]["teal-6"],
                ordinal=palette["schemes"]["teal-6"],
                ramp=palette["schemes"]["teal-6"],
            ),
        )
    )