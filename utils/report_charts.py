"""Plain-words explanations for every chart in Meridian's HTML report.

One list, used by the Meridian charts page and by the guided tour, so the two
never drift apart. `group` is the section the chart sits in.
"""

MODEL_CHARTS = [
    dict(id="expected_actual", group="Does the model fit?", icon="show_chart",
         title="Real sales vs. the model's guess",
         what="Two lines, one for real sales each week and one for the sales the model expected. "
              "The lowest line is the baseline: the sales you would get with no ads at all.",
         read="If the real and expected lines stay close, the model has learned how your sales move. "
              "Big gaps in a few weeks usually mean something happened that the data doesn't show, like a stock-out."),
    dict(id="fit_table", group="Does the model fit?", icon="table_chart",
         title="Fit scores",
         what="Three numbers that grade the model. R-squared is the share of week-to-week change it explains. "
              "MAPE is how far off it is in an average week. wMAPE is the same, but big weeks count more.",
         read="R-squared close to 1 is good. MAPE and wMAPE under 10% are good for weekly sales."),
    dict(id="channel_drivers", group="Where did sales come from?", icon="stacked_bar_chart",
         title="What made up total sales",
         what="Each bar is one piece of your sales: the baseline (sales with no ads) and what each channel "
              "added, biggest first. The pieces add up to 100%.",
         read="The longer a channel's bar, the more sales it brought in. It says nothing yet about cost; "
              "that comes in the ROI charts."),
    dict(id="contribution_pie", group="Where did sales come from?", icon="donut_large",
         title="Share of sales",
         what="The whole circle is all your sales, split in two: the share your ads brought in (all channels "
              "together) and the baseline that would have happened anyway.",
         read="The bigger the ads slice, the more your sales depend on marketing. Many businesses have a big "
              "baseline, because loyal customers buy with or without ads."),
    dict(id="spend_outcome", group="Where did sales come from?", icon="balance",
         title="Share of money vs. share of sales",
         what="For each channel, one bar is its share of the ad budget and the other is its share of the sales "
              "the ads brought in. The green mark is its ROI.",
         read="When a channel's sales bar is longer than its money bar, it brings in more than its share of the "
              "budget. Those channels are cheap for what they do."),
    dict(id="contrib_by_time", group="Where did sales come from?", icon="area_chart",
         title="Sales from each channel, week by week",
         what="Each colored band is the extra sales from one channel in each week.",
         read="A band that gets thicker means that channel brought in more in those weeks, often because you "
              "spent more on it then."),
    dict(id="contrib_rank", group="Where did sales come from?", icon="leaderboard",
         title="Which channel ranked first, over time",
         what="Each line is one channel's rank by extra sales, from one period to the next. Rank 1 brought in the most.",
         read="Lines that cross mean channels swapped places. A channel that stays at the top is your steady earner."),
    dict(id="roi_channel", group="What does each $1 bring back?", icon="bar_chart",
         title="Money back for every $1 (ROI)",
         what="One bar per channel. The height is the sales each $1 of spend brought back. The thin line on top "
              "is the range the true value is likely in.",
         read="Above 1 means the channel paid for itself. A long thin line means the model isn't sure, often "
              "because spend on that channel barely changed."),
    dict(id="roi_effectiveness", group="What does each $1 bring back?", icon="bubble_chart",
         title="Return vs. effect per ad",
         what="Each bubble is a channel. Higher means more money back per $1. Further right means more sales "
              "for each ad people saw. Bigger bubbles had more spend.",
         read="Bubbles up and to the right are working best. A big bubble low on the chart is a lot of money "
              "for a small return."),
    dict(id="roi_marginal", group="What does each $1 bring back?", icon="trending_up",
         title="Return now vs. return on the next $1",
         what="Each bubble is a channel. Across is the average return so far. Up is the return on the next "
              "dollar you add.",
         read="High bubbles can still take more money. Bubbles near the bottom are close to full: more money "
              "there buys little."),
    dict(id="cpik_channel", group="What does each $1 bring back?", icon="payments",
         title="Cost to bring in $1 of extra sales",
         what="ROI turned upside down: how much you pay, on each channel, to bring in one more dollar of sales.",
         read="Shorter bars are cheaper. Under $1 means the channel earns back more than it costs."),
    dict(id="response_curves", group="When does more money stop helping?", icon="ssid_chart",
         title="What happens if you spend more or less",
         what="One curve per channel: the sales it brings at different spend levels, from nothing up to double "
              "what you spend now.",
         read="Steep parts mean more money still brings more sales. Where a curve flattens out, the channel is "
              "full and extra money mostly goes to waste."),
]

PLAN_CHARTS = [
    dict(id="spend_delta", group="Budget plan", icon="swap_vert",
         title="How the plan moves money",
         what="One bar per channel: how much more or less money it gets in the plan.",
         read="Bars above zero get more money, bars below give some up. The total budget stays the same."),
    dict(id="spend_allocation", group="Budget plan", icon="pie_chart",
         title="The planned budget split",
         what="The whole circle is the planned budget. Each slice is one channel's share.",
         read="Compare it with how you split money today to see the change at a glance."),
    dict(id="outcome_delta", group="Budget plan", icon="trending_up",
         title="Extra sales from the plan",
         what="The first bar is the sales your ads bring in with today's split. Each step after it is one "
              "channel's change under the plan, up or down. The last bar is the sales with the plan.",
         read="Some channels lose a little and others gain more. The gap between the first and last bar is "
              "what the whole plan adds."),
    dict(id="optimized_curves", group="Budget plan", icon="ssid_chart",
         title="The plan on each response curve",
         what="The same curves as before, with marks for today's spend and for the planned spend.",
         read="The plan moves money off the flat parts of curves and onto the steep parts."),
]
