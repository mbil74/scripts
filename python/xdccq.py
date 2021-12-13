# coding=UTF-8

SCRIPT_NAME    = "xdccq"
SCRIPT_AUTHOR  = "Randall Flagg <shinigami_flagg@yahoo.it>"
SCRIPT_VERSION = "0.1.2"
SCRIPT_LICENSE = "GPL3"
SCRIPT_DESC    = "Queue Xdcc messages to bots"

import_ok = True

try:
    import weechat
except ImportError:
    print("This script must be run under WeeChat.")
    print("Get WeeChat now at: http://www.weechat.org/")
    import_ok = False

schedule = {}
# create a dictionary to save botnames and packs
# botname = {"botname1":"pack1","botname2":"pack2"}
# print myDict["jeff"] # => "jeffs value"
# print myDict.keys() # => ["john", "jeff"]

channel = ""


def xdccq_help_cb(data, buffer, args):
    """Callback for /xdccq command."""
    global channel, schedule
    response = {
        'add', 'list', 'listall', 'clear', 'clearall',
    }
    if args:
        words = args.strip().split(' ')
        if words[0] in response:
            if words[0] == "add":
                channel = buffer
                botname = words[1]
                newpacks = numToList(words[2])

                if botname in schedule:
                    packs = schedule[botname]
                else:
                    packs = []

                packs.extend(newpacks)
                schedule.update({botname : packs})
                # look for packs aldready added
                # if already in transfer just add to list
                # else add and start transfer

                # check if bot is in auto accept nicks
                autonicks = weechat.config_string(weechat.config_get("xfer.file.auto_accept_nicks")).split(",")

                if not botname in autonicks:
                    xfer_option = weechat.config_get("xfer.file.auto_accept_nicks")
                    newlist = weechat.config_string(xfer_option)+","+botname

                    rc = weechat.config_option_set(xfer_option, newlist, 1)
                    if rc == weechat.WEECHAT_CONFIG_OPTION_SET_OK_CHANGED:
                        weechat.prnt('', "%s added to xdcc auto-accept list" % botname)
                    elif rc == weechat.WEECHAT_CONFIG_OPTION_SET_OK_SAME_VALUE:
                        weechat.prnt('', "%s already in xdcc auto-accept list" % botname)
                    elif rc == weechat.WEECHAT_CONFIG_OPTION_SET_ERROR:
                        weechat.prnt('', "Error in adding %s in auto-accept list" % botname)
                else:
                    weechat.prnt('', "%s already in xdcc auto-accept nicks, not added." % botname)

                if len(packs):
                    runcommands(botname)
                    pass
            elif words[0] == "list":
                if len(words) > 1:
                    botname = words[1]
                    if botname in schedule:
                        packs = schedule[botname]
                        weechat.prnt('',"%s packs left" % len(packs))
                        weechat.prnt('',"from %s bot" % words[1])
                    else:
                        weechat.prnt('',"%s not in queue. Can't list!" % botname)
                else:
                    weechat.prnt('', "No bot specified. Scheduled packs : %s" % schedule)
            elif words[0] == "listall":
                weechat.prnt('', "scheduled packs : %s" % schedule)
            elif words[0] == "clear":
                if len(words) > 1:
                    botname = words[1]
                    if botname in schedule:
                        schedule.update({botname : []})
                    else:
                        weechat.prnt('',"%s not in queue. Can't clear!" % botname)
                else:
                    weechat.prnt('',"No bot specified. Can't clear!")
            elif words[0] == "clearall":
                schedule = {}
                weechat.prnt('', "Queue cleared")
        else:
            weechat.prnt('', "xdccq error: %s not a recognized command. Try /help xdccq" % words[0])

    return weechat.WEECHAT_RC_OK


def numToList(string):
    """Converts a string like '3,5,7-9,14' into a list."""
    ret = []
    numsplit = string.split(",")
    # the following code makes nums into a list of all integers
    for n in numsplit:
        nr = n.split('-')
        # handle the case of a single number
        if len(nr) == 1:
            try:
                ret.append(int(n))
            except:
                raise ValueError("number")
        # handle the case of a range
        elif len(nr) == 2:
            try:
                low = int(nr[0])
                nx = nr[1].split("%", 1)
                if len(nx) == 1:
                    high = int(nr[1]) + 1
                    step = 1
                else:
                    high = int(nx[0]) + 1
                    step = int(nx[1])
                if low > high:
                    raise ValueError("number")
                ret += range(low, high, step)
            except ValueError:
                raise ValueError("number")
        else:
            raise ValueError("range")
    return ret


def runcommands(botname):
    global channel, schedule

    if botname in schedule:
        pack = schedule[botname]

        weechat.prnt('', "Pack %s remaining" % pack)
        weechat.prnt('', "botname = %s" % botname)
        weechat.prnt('', "schedule = %s" % schedule)

        if len(pack):
            onepack = pack.pop(0)
            cmd = "/msg " + botname + " xdcc send " + str(onepack)
            weechat.command(channel, cmd)
            schedule.update({botname : pack})

    return weechat.WEECHAT_RC_OK


def xfer_ended_signal_cb(data, signal, signal_data):
    # at the end of transfer print the botname and completed file
    weechat.infolist_next(signal_data)
    # status_string = weechat.infolist_string(signal_data, 'status_string'),
    # filename = weechat.infolist_string(signal_data, 'filename'),
    # local_filename = weechat.infolist_string(signal_data, 'local_filename'),
    # size = weechat.infolist_string(signal_data, 'size'),
    botname = weechat.infolist_string(signal_data, 'remote_nick'),
    weechat.prnt("", "remote_nick = %s" % botname)

    runcommands(''.join(botname))
    return weechat.WEECHAT_RC_OK


if __name__ == "__main__" and import_ok:
    weechat.register(SCRIPT_NAME, SCRIPT_AUTHOR, SCRIPT_VERSION, SCRIPT_LICENSE, SCRIPT_DESC, "", "")
    weechat.hook_command(
            SCRIPT_NAME, SCRIPT_DESC,
            '\nadd [name] packs\n list\n listall [name]\n clear\n clearall [name]',
            'ADD: adds packs to [botname] queue  \n LIST: list [botname] queue \n Pack format can be 1-10 or 1,2,3 or 1-10,12,15 \n LISTALL: list all queue \n CLEAR: clean all queues \n CLEARALL: clears queue for [botname]',
            'add %(nick) packs'
            ' || list  %(nick)'
            ' || listall'
            ' || clear %(nick)'
            ' || clearall',
            'xdccq_help_cb', '')
    weechat.hook_signal("xfer_ended", "xfer_ended_signal_cb", "")
