from test_pychat import PyServer


# Define commands


def add(**command_data):    # ** operator required if return_data=True
    try:
        result = f">> {str(int(command_data['args'][1]) + int(command_data['args'][2]))}"
    except ValueError:
        s.targeted_send("[Server] Expected an integer", command_data['user'])
    else:
        s.targeted_send(result, command_data['user'])

    '''

                --===RETURNED DATA===--
        
        Data is passed into the function as a dictionary the keys are:
            
           | 'args': list of arguments starting with the command itself 
           | 'user': the user object of the client who called the command

    '''


def stat():  # If return_data=False use no parameters
    s.broadcast('[Server] Someone asked if I was online!')


# Create PyServer object
s = PyServer(9090, "1234", 'log.txt', rsa_keys_size=4096/4)

# Set command prefix
s.set_command_prefix('/')
s.set_message_prefix('[%u @ %H:%M] ')

'''

    --===FORMAT CODES FOR MESSAGE PREFIX===--

    >> User Data
        %u | user ip

    >> Time & Date
        %H | current hour (24hr)
        %M | current minute (24hr)
        
    >> Other
        %% | escape '%'
        
'''

# Create commands
s.make_command('add', add, return_data=True, expected_args=3)
s.make_command('stat', stat, return_data=False)

# Start accepting clients
s.start_thread()
