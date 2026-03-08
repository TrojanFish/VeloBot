# --- en Localization ---
LOCALIZATION = \
{   'achievement_unlocked': '🎉 **Achievement Unlocked!** 🎉\n'
                            '\n'
                            'Congratulations on earning the **{name}** achievement!\n'
                            '_{desc}_',
    'activity_detail_avg_cadence': '🦶 Avg Cadence',
    'activity_detail_avg_hr': '❤️ Avg Heartrate',
    'activity_detail_avg_power': '🔌 Avg Power',
    'activity_detail_avg_speed': '💨 Avg Speed',
    'activity_detail_calories': '🔥 Calories',
    'activity_detail_dist': '📏 Distance',
    'activity_detail_elev': '🧗 Elevation',
    'activity_detail_max_speed': '⚡️ Max Speed',
    'activity_detail_suffer_score': '🎯 Suffer Score',
    'activity_detail_time': '⏱️ Time',
    'activity_suffer_easy': '😌 Easy Recovery',
    'activity_suffer_high': '🔥 High Intensity',
    'activity_suffer_intense': '🥵 Extreme Intensity',
    'activity_suffer_medium': '💪 Medium Intensity',
    'activity_type_climb': '⛰️ Climbing',
    'activity_type_flat': '🚵 Flat Ride',
    'activity_type_hilly': '🌄 Hilly Ride',
    'activity_view_on_strava': 'View on Strava',
    'back_to_menu': '⬅️ Back to Menu',
    'create_ride_cancel': 'Creation of the group ride has been cancelled.',
    'create_ride_desc_ok': 'The group ride has been successfully published to the group!',
    'create_ride_route_ok': 'Got it! Lastly, are there any [Additional Notes]? (e.g., intensity, '
                            "precautions. Reply 'none' if not applicable).",
    'create_ride_start': "Alright! Let's create a new group ride. What is the [Title] for this "
                         'ride?',
    'create_ride_time_error': 'The time format is incorrect. Please re-enter in YYYY-MM-DD HH:MM '
                              'format.',
    'create_ride_time_ok': 'Time received! Next, what is the [Meeting Point or Route Link]?',
    'create_ride_title_ok': 'Great title! Now, please tell me the [Time] for the ride in '
                            'YYYY-MM-DD HH:MM format (e.g., 2025-09-27 08:00).',
    'fetching_video': 'Fetching the latest YouTube video, please wait...',
    'get_last_activity': 'Last Activity',
    'help_text': 'I can help you monitor and push:\n'
                 '🚴\u200d♂️ Latest Strava activities\n'
                 '📺 New YouTube videos\n'
                 '\n'
                 'Here are the available commands:\n'
                 '\n'
                 '/link_strava - Connect your Strava account.\n'
                 '/toggle_strava_privacy - Switch activity push mode (public/private).\n'
                 '/get_last_activity - See your last activity.\n'
                 '/get_last_video - Get the latest YouTube video.\n'
                 '/report - Get your personal weekly summary.\n'
                 "/leaderboard - View the group's weekly honor roll.\n"
                 '/create_ride - Organize a group ride.\n'
                 '/my_rides - See your upcoming rides.\n'
                 '/my_achievements - View your achievements.\n'
                 '/weather `[city]` - Get a weather forecast.\n'
                 '/route `[location]` - Find cycling routes.\n'
                 '/language - Switch language.\n'
                 '/menu - Open the main Control Panel.',
    'language': 'Language',
    'language_prompt': 'Please select your preferred language:',
    'language_set': '✅ Language has been set to {lang}.',
    'last_activity_error': 'An error occurred while fetching activity data. Please try again '
                           'later.',
    'last_activity_not_found': 'No activities found in your Strava account.',
    'last_activity_sent_privately': 'I have sent your latest activity to you via private message.',
    'leaderboard': 'Leaderboard',
    'leaderboard_anonymous_user': 'Anonymous Rider',
    'leaderboard_climb_king': '🧗 King of Climbing',
    'leaderboard_dist_king': '📏 King of Distance',
    'leaderboard_no_activity': 'No one has uploaded any activities in the past 7 days. Looking '
                               'forward to your performance!',
    'leaderboard_time_king': '⏱️ King of Effort',
    'leaderboard_title': "🏆 *This Week's Group Honor Roll (Last 7 Days)*\n",
    'link_strava_button': 'Authorize Strava',
    'link_strava_prompt': 'Please click the button below to authorize the bot to access your '
                          'Strava activity data:',
    'location_button_route': '🗺️ Find Routes',
    'location_button_weather': '🌦️ Get Weather',
    'location_expired': 'Sorry, the location information has expired. Please share your location '
                        'again.',
    'location_fetching_route': 'Okay, generating route links for you...',
    'location_fetching_weather': 'Okay, fetching the weather forecast...',
    'location_received': "I've received your location. What would you like to do?",
    'maintenance': 'Gear Maintenance',
    'maintenance_no_gear': 'No gear linked yet. Try syncing activities first.',
    'maintenance_set_success': '✅ Maintenance threshold set for {gear_name} ({part}): {threshold} '
                               'km',
    'maintenance_title': '🔧 *Gear Maintenance Center*',
    'menu_activity': 'Activity',
    'menu_awards': 'Awards',
    'menu_gear': 'Gear',
    'menu_settings': 'Settings',
    'menu_stats': 'Statistics',
    'menu_subtitle': 'Select a category to manage your cycling data and settings:',
    'menu_title': 'Dashboard',
    'menu_tools': 'Tools',
    'my_achievements': 'Achievements',
    'my_achievements_no_activity': "You haven't unlocked any achievements yet. Keep riding!",
    'my_achievements_title': '🏅 *My Hall of Achievements*\n',
    'my_rides': 'My Rides',
    'my_rides_creator': ' (You are the organizer)',
    'my_rides_no_activity': 'You have no upcoming rides scheduled.',
    'my_rides_sent_privately': 'I have sent your ride list to you via private message.',
    'my_rides_title': '🗓️ *Your Upcoming Rides:*\n',
    'new_video_notification': '📢 **{author}** has published a new video!\n\n🎬 **Title:** {title}',
    'privacy_not_linked': "You haven't linked your Strava account yet. Please use /link_strava "
                          'first.',
    'privacy_switched_private': '✅ Your Strava activity push mode has been switched to [Private].\n'
                                'New activities will be sent to you via private message only.',
    'privacy_switched_public': '✅ Your Strava activity push mode has been switched to [Public].\n'
                               'New activities will be pushed to the group.',
    'reauth_required': 'The bot could not access your Strava data, possibly because the '
                       'authorization has expired. Please use /link_strava to re-authorize.',
    'report': 'Weekly Report',
    'report_dist': '📏 *Total Distance*: {dist:.2f} km{comparison}',
    'report_elev': '🧗 *Total Elevation*: {elev:.0f} m{comparison}',
    'report_monthly_no_activity': 'You have no recorded activities in the past month. Keep it up!',
    'report_monthly_title': '📊 *Your Personal Monthly Report*\n',
    'report_no_activity': 'You have no recorded activities in the past 7 days. Keep it up!',
    'report_rides': '🚴\u200d♂️ *Activities*: {count} times{comparison}',
    'report_time': '⏱️ *Total Time*: {time}{comparison}',
    'report_title': '📊 *Your Personal Weekly Report (Last 7 Days)*\n',
    'report_yearly_no_activity': 'You have no recorded activities in the past year. Keep it up!',
    'report_yearly_title': '📊 *Your Personal Yearly Report*\n',
    'ride_card_creator': '👑 *Organizer*: {name}',
    'ride_card_desc': '📝 *Notes*: {desc}',
    'ride_card_invalid': 'This ride information is no longer valid.',
    'ride_card_join': 'Join 🚴',
    'ride_card_leave': 'Leave 🚶',
    'ride_card_no_participants': 'None yet',
    'ride_card_participants': '\n👥 *Joined ({count})*: {names}',
    'ride_card_route': '📍 *Route*: {route}',
    'ride_card_time': '📅 *Time*: {time}',
    'route': 'Find Routes',
    'route_error': 'Failed to get location information. Please try again later.',
    'route_google_maps': 'View in Google Maps',
    'route_komoot': 'Plan a route in Komoot',
    'route_location_not_found': 'Location not found: {location}',
    'route_prompt': 'Please provide a location, e.g., `/route Central Park`, or share your '
                    'location directly.',
    'route_recommendation': 'Here are some recommended platforms for you to explore routes:',
    'start_welcome': "👋 Welcome! I'm the community bot. Use /help to see what I can do.",
    'strava_auth_success': '✅ Authorization successful! {athlete_name}, your Strava account is now '
                           'linked.\n'
                           '\n'
                           'By default, activities will be sent to you via private message only. '
                           'To change this, use the /toggle_strava_privacy command.',
    'sync_started': '🔄 Starting synchronization... please wait.',
    'sync_strava': 'Sync Strava Data',
    'sync_success': '✅ Synchronization complete! Your gear and recent activities are now up to '
                    'date.',
    'toggle_strava_privacy': 'Privacy Mode',
    'units': 'Units',
    'units_prompt': 'Please select your preferred unit system:',
    'units_set_success': '✅ Unit system has been set to {unit}.',
    'video_error': 'An error occurred while fetching the video. Please try again later.',
    'video_not_found': 'Could not retrieve video from the RSS feed.',
    'weather': 'Weather',
    'weather_city_not_found': 'City not found: {city}',
    'weather_current': '**Current**: {temp:.0f}°C, 💨 {windspeed:.1f} km/h\n',
    'weather_fetching_city_error': 'Failed to get weather information. Please check the city name '
                                   'or try again later.',
    'weather_forecast': '**Next 24 Hours**:',
    'weather_processing_error': 'An internal error occurred while processing weather data.',
    'weather_prompt': 'Please provide a city name, e.g., `/weather London`, or share your location '
                      'directly.',
    'weather_title': '*{city_name} Weather Forecast* for Cycling\n',
    'welcome_new_member': 'Hey {mention}, welcome to our cycling family! 🚴\u200d♀️🚴\u200d♂️\n'
                          '\n'
                          'Great to have another rider on the road with us! To help everyone get '
                          'to know you, feel free to share a bit about yourself:\n'
                          "• What's your ride? (Road/MTB/Gravel/...)\n"
                          '• Where do you usually cycle?\n'
                          '\n'
                          "I'm the group's bot assistant. Send me a /start to see all my "
                          'features!\n'
                          '\n'
                          '---\n'
                          '\n'
                          '为了方便交流，您可以使用 /language 命令将我切换为中文模式。',
    'your_last_activity_is': 'Your last activity was:\n'}

LOCALIZED_COMMANDS = \
{   'add_rss': '➕ Add an RSS feed to monitor',
    'create_ride': '🤝 Organize a group ride',
    'get_last_activity': '🚴 View your most recent Strava activity',
    'get_last_video': '📺 Get the latest YouTube video',
    'help': 'ℹ️ Show the detailed command list',
    'language': '🌐 Switch Language',
    'leaderboard': "🏆 View the group's honor roll",
    'link_strava': '🔗 Link or re-authorize your Strava account',
    'list_rss': '📜 List your RSS subscriptions',
    'maintenance': '🔧 Gear maintenance tracking',
    'menu': '⚙️ Open the main Control Panel',
    'my_achievements': '🏅 View your achievements',
    'my_rides': "🗓️ View the rides you've joined",
    'remove_rss': '🗑 Remove an RSS feed',
    'report': '📊 Get your personal weekly report',
    'route': '🗺️ Find cycling routes',
    'start': '🚀 Show a brief welcome message',
    'sync_strava': '🔄 Sync Strava activities & gear manually',
    'toggle_strava_privacy': '🔒 Toggle activity push mode (public/private)',
    'units': '📏 Switch units (km/mi)',
    'weather': '🌦️ Get a weather forecast'}

LOCALIZED_ACHIEVEMENTS = \
{   'dist_100k': {   'desc': 'First time completing a single ride over 100km',
                     'name': '💯 100k Certified'},
    'elev_1000m': {   'desc': 'First time completing an activity with over 1000m of elevation gain',
                      'name': '🧗\u200d♂️ Climbing Pro'},
    'elev_2000m': {   'desc': 'First time reaching over 2000m of elevation gain in a single ride',
                      'name': '🏔 King of the Hill'},
    'max_speed_70k': {   'desc': 'First time reaching a max speed over 70km/h',
                         'name': '⚡️ Speed Legend'},
    'month_dist_500k': {'desc': 'Rode over 500km in a single month', 'name': '📅 Monthly Century'},
    'total_dist_10000k': {   'desc': 'Total cycling distance reached 10,000km',
                             'name': '👑 Titan of 10,000k'},
    'total_dist_1000k': {   'desc': 'Total cycling distance reached 1000km',
                            'name': '🌍 A Thousand Miles'},
    'total_dist_5000k': {   'desc': 'Total cycling distance reached 5000km',
                            'name': '🚴\u200d♂️ Knight of Ten Thousand Miles'},
    'year_dist_10000k': {   'desc': 'Rode over 10,000km in a single year',
                            'name': '🏆 Legend of the Year'}}
