/*
 * [COPYRIGHT]
 *
 * [NAME] is free software; you can redistribute it and/or modify it
 * under the terms of the GNU Lesser General Public License as
 * published by the Free Software Foundation; either version 2.1 of
 * the License, or (at your option) any later version.
 *
 * This software is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
 * Lesser General Public License for more details.
 *
 * You should have received a copy of the GNU Lesser General Public
 * License along with this software; if not, write to the Free
 * Software Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA
 * 02110-1301 USA, or see the FSF site: http://www.fsf.org.
 */

package org.gem.engine.core.event;

/**
 * Raised when a client is trying to raise or register listeners to an unknown event.
 * 
 * @author Andrea Cerisara
 * @version $Id: UnknownEventException.java 546 2010-07-09 08:40:15Z acerisara $
 */
public class UnknownEventException extends RuntimeException
{

    private static final long serialVersionUID = -5951849611850994774L;

    private final String event;

    /**
     * @param event the event name
     */
    public UnknownEventException(String event)
    {
        this.event = event;
    }

    @Override
    public String getMessage()
    {
        return "Event " + event + " is not registered. You have to register the event with canRaise(" + event
                + "); in order to attach listeners to this event.";
    }

}
